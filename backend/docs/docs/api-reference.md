# Référence API

Cette page affiche la référence interactive complète de l'API NewsFoundry, générée automatiquement depuis la spec OpenAPI du backend.

!!! warning "Environnement local requis"
    Le Swagger UI ci-dessous pointe sur `http://localhost:8000/openapi.json`.
    **Le backend doit être lancé localement** pour qu'il soit fonctionnel.

    Pour un environnement déployé, remplacez l'URL dans le script ci-dessous par l'URL de votre instance (ex. `https://api.mondomaine.com/openapi.json`).

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
        SwaggerUIBundle.presets.apis
      ],
      layout: "BaseLayout"
    });
  };
</script>
