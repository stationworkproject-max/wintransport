-- ==============================================================================
-- WINTRANSPORT TUNISIA — OVER-THE-AIR (OTA) DYNAMIC DATASET MIGRATION
-- Enables live updates for Lines, Stops, and GeoJSON shapes pushed from Studio
-- Zero rebuild needed for Android and Web apps
-- ==============================================================================

-- 1. DATASET METADATA TABLE
CREATE TABLE IF NOT EXISTS public.transit_dataset_meta (
    version INT PRIMARY KEY,
    description TEXT DEFAULT '',
    lines_url TEXT NOT NULL,
    shapes_url TEXT NOT NULL,
    lines_count INT NOT NULL DEFAULT 0,
    shapes_count INT NOT NULL DEFAULT 0,
    checksum TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for instant latest version query
CREATE INDEX IF NOT EXISTS idx_transit_dataset_version ON public.transit_dataset_meta (version DESC);

-- 2. CREATE PUBLIC STORAGE BUCKET FOR TRANSIT ASSETS
INSERT INTO storage.buckets (id, name, public)
VALUES ('transit-assets', 'transit-assets', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- 3. STORAGE POLICIES (Read for everyone, upload for Studio)
DROP POLICY IF EXISTS "Public Read Transit Assets" ON storage.objects;
CREATE POLICY "Public Read Transit Assets" 
ON storage.objects FOR SELECT 
USING (bucket_id = 'transit-assets');

DROP POLICY IF EXISTS "Studio Upload Transit Assets" ON storage.objects;
CREATE POLICY "Studio Upload Transit Assets" 
ON storage.objects FOR INSERT 
WITH CHECK (bucket_id = 'transit-assets');

DROP POLICY IF EXISTS "Studio Update Transit Assets" ON storage.objects;
CREATE POLICY "Studio Update Transit Assets" 
ON storage.objects FOR UPDATE 
USING (bucket_id = 'transit-assets');

-- 4. RPC TO PUBLISH / BUMP DATASET VERSION ATOMICALLY
CREATE OR REPLACE FUNCTION public.publish_transit_dataset(
    p_version INT,
    p_description TEXT DEFAULT '',
    p_lines_url TEXT DEFAULT '',
    p_shapes_url TEXT DEFAULT '',
    p_lines_count INT DEFAULT 0,
    p_shapes_count INT DEFAULT 0,
    p_checksum TEXT DEFAULT ''
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO public.transit_dataset_meta (
        version,
        description,
        lines_url,
        shapes_url,
        lines_count,
        shapes_count,
        checksum,
        created_at
    ) VALUES (
        p_version,
        p_description,
        p_lines_url,
        p_shapes_url,
        p_lines_count,
        p_shapes_count,
        p_checksum,
        NOW()
    )
    ON CONFLICT (version) DO UPDATE SET
        description = EXCLUDED.description,
        lines_url = EXCLUDED.lines_url,
        shapes_url = EXCLUDED.shapes_url,
        lines_count = EXCLUDED.lines_count,
        shapes_count = EXCLUDED.shapes_count,
        checksum = EXCLUDED.checksum,
        created_at = NOW();

    RETURN jsonb_build_object(
        'success', true,
        'version', p_version,
        'timestamp', NOW()
    );
END;
$$;

-- 5. GRANT PERMISSIONS FOR POSTGREST ACCESS
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.transit_dataset_meta TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.publish_transit_dataset TO anon, authenticated;

-- Disable RLS on dataset_meta so anonymous reads never fail
ALTER TABLE public.transit_dataset_meta DISABLE ROW LEVEL SECURITY;
