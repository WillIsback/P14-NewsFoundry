/**
 * Brief: Ajoute un timeout à une promesse existante
 * @param {Promise} promise - La promesse à chronométrer
 * @param {number} ms - Temps limite en millisecondes (défaut: 30000)
 * @returns {Promise} Promesse qui se résout ou rejette selon le timeout
 */
export function withTimeout(promise, ms = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), ms);

    return Promise.race([
        promise,
        new Promise((_, reject) => {
            controller.signal.addEventListener('abort', () => {
                reject(new Error(`Timeout après ${ms}ms`));
            });
        })
    ]).finally(() => clearTimeout(timeoutId));
}


/*
    fonction générique Request pour les differentes opérations CRUD
*/
/**
 * Brief: Fonction générique pour effectuer des requêtes HTTP vers l'API backend
 *
 * @param {string} endpoint - Endpoint de l'API à appeler (relatif à l'URL de base)
 * @param {Object} payload - Configuration de la requête {method, headers, body, authorization}
 * @param {string} baseUrl - Configuration de l'url de base
 * @returns {Request} Objet Request configuré pour l'appel à l'API
 */
export const request = (baseUrl: string, endpoint: string, payload: any) => {
    const { method, headers, body } = payload
    const request = new Request(`${baseUrl}${endpoint}`, {
        method: method,
        headers: headers,
        body: body,
    })
    // console.log('request : ', request)
    return request

}