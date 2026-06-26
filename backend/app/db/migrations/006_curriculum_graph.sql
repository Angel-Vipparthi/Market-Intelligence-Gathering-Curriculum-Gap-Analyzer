-- ============================================================================
-- Migration 006: Curriculum Graph
-- Description: Knowledge graph tables for curriculum structure and relationships.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Nodes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_graph_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type       VARCHAR(100) NOT NULL
                        CHECK (node_type IN (
                            'course',
                            'learning_path',
                            'module',
                            'session',
                            'topic',
                            'subtopic',
                            'project',
                            'coding_challenge',
                            'assessment',
                            'quiz',
                            'tool',
                            'framework',
                            'version',
                            'market_signal',
                            'curriculum_gap'
                        )),
    name            VARCHAR(1000) NOT NULL,
    properties      JSONB,
    document_id     UUID REFERENCES curriculum_documents(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Node indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_node_type
    ON curriculum_graph_nodes (node_type);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_name
    ON curriculum_graph_nodes (name);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_properties
    ON curriculum_graph_nodes USING GIN (properties);

-- ---------------------------------------------------------------------------
-- Edges
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_graph_edges (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id      UUID NOT NULL REFERENCES curriculum_graph_nodes(id) ON DELETE CASCADE,
    target_node_id      UUID NOT NULL REFERENCES curriculum_graph_nodes(id) ON DELETE CASCADE,
    relationship_type   VARCHAR(100) NOT NULL
                            CHECK (relationship_type IN (
                                'PREREQUISITE_OF',
                                'PART_OF',
                                'USES_TOOL',
                                'USES_VERSION',
                                'TESTED_BY',
                                'PRACTICED_BY',
                                'IMPLEMENTS',
                                'DEPENDS_ON',
                                'IMPACTS',
                                'COVERS'
                            )),
    properties          JSONB,
    weight              FLOAT DEFAULT 1.0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_graph_edge UNIQUE (source_node_id, target_node_id, relationship_type)
);

-- Edge indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_source_node_id
    ON curriculum_graph_edges (source_node_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_target_node_id
    ON curriculum_graph_edges (target_node_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_relationship_type
    ON curriculum_graph_edges (relationship_type);

-- ---------------------------------------------------------------------------
-- Graph traversal function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION find_connected_nodes(
    start_node_id UUID,
    rel_type VARCHAR,
    max_depth INT DEFAULT 3
)
RETURNS TABLE (
    id              UUID,
    node_type       VARCHAR(100),
    name            VARCHAR(1000),
    properties      JSONB,
    depth           INT
)
LANGUAGE sql STABLE
AS $$
    WITH RECURSIVE traversal AS (
        -- Base case: the start node
        SELECT
            n.id,
            n.node_type,
            n.name,
            n.properties,
            0 AS depth
        FROM curriculum_graph_nodes n
        WHERE n.id = start_node_id

        UNION ALL

        -- Recursive case: follow edges of the given relationship type
        SELECT
            n.id,
            n.node_type,
            n.name,
            n.properties,
            t.depth + 1
        FROM traversal t
        JOIN curriculum_graph_edges e
            ON e.source_node_id = t.id
            AND e.relationship_type = rel_type
        JOIN curriculum_graph_nodes n
            ON n.id = e.target_node_id
        WHERE t.depth < max_depth
    )
    SELECT DISTINCT
        traversal.id,
        traversal.node_type,
        traversal.name,
        traversal.properties,
        traversal.depth
    FROM traversal
    ORDER BY traversal.depth;
$$;
