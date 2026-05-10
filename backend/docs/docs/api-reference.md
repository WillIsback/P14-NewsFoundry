# Référence API

Cette page affiche la référence interactive complète de l'API NewsFoundry, générée automatiquement depuis la spec OpenAPI du backend.

> **Prérequis :** Le backend doit être lancé localement sur `http://localhost:8000` pour que le Swagger UI ci-dessous soit fonctionnel en développement. En production, pointer l'URL vers le backend Railway déployé.

---

<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">

<div id="swagger-ui" style="margin-top: 1rem;"></div>

<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.onload = function() {
    SwaggerUIBundle({
      url: "http://localhost:8000/openapi.json",
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ],
      layout: "StandaloneLayout"
    });
  };
</script>

---

*Pour pointer vers un backend distant, remplacer l'URL `http://localhost:8000/openapi.json` par l'URL de votre instance déployée.*
