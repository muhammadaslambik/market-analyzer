export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Set CORS headers agar UI frontend bisa mengakses API ini
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    // Tangani preflight request untuk CORS
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // 1. Endpoint Check Kesehatan Sistem
      if (path === "/api/health") {
        return new Response(JSON.stringify({ status: "healthy", timestamp: new Date().toISOString() }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 2. Endpoint Mengambil Data Ringkasan Performa (Track Record)
      if (path === "/api/track-record") {
        // Query langsung ke Cloudflare D1
        const { results } = await env.DB.prepare(
          "SELECT * FROM track_record ORDER BY symbol ASC, horizon ASC"
        ).all();

        return new Response(JSON.stringify({ success: true, data: results }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 3. Endpoint Jika Rute Tidak Ditemukan
      return new Response(JSON.stringify({ error: "Endpoint tidak ditemukan" }), {
        status: 404,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }
  }
};
