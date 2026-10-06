// Definisi tipe data untuk Environment D1 Cloudflare
export interface Env {
  DB: D1Database;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Headers CORS agar UI Frontend bisa memanggil API
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
      // 1. Endpoint Cek Kesehatan Worker
      if (path === "/api/health") {
        return new Response(JSON.stringify({ status: "healthy", timestamp: new Date().toISOString() }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 2. Endpoint Mengambil Data Track Record dari D1
      if (path === "/api/track-record") {
        const { results } = await env.DB.prepare(
          "SELECT * FROM track_record ORDER BY symbol ASC, horizon ASC"
        ).all();

        return new Response(JSON.stringify({ success: true, data: results }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 3. Rute Tidak Ditemukan
      return new Response(JSON.stringify({ error: "Endpoint tidak ditemukan" }), {
        status: 404,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });

    } catch (error: any) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }
  }
};
