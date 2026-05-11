import { withTimeout, request } from "@/src/lib/server.lib"
import { bodyLoginForAccessTokenApiV1AuthLoginPostSchema } from "../models/gen"
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api"

export async function postLogin(email : string, password: string) {
    const route = "auth/login"
    // Validation des paramètres
    if (typeof email !== "string" || typeof password !== "string") {
        const error = {
            user: "Veuillez remplir tous les champs",
            dev: "Invalid parameters: email and password must be strings"
        }
        console.error("[postLogin]", error.dev)
        return { success: false, error }
    }

    try {
        const response = await withTimeout(
            fetch(request(BACKEND_URL, route, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    email: email,
                    password: password,
                })
            })),
            10000 // 10s max
        );

        // Gestion des erreurs HTTP
        if (!response.ok) {
            const errorMessages = getErrorMessage(response.status)
            console.error("[postLogin]", errorMessages.dev)
            return { success: false, error: errorMessages }
        }

        // Succès
        const data = await response.json()
        // console.log('data reçu : ', data)
        return { success: true, data }

    } catch (error) {
        // Erreurs réseau ou parsing JSON
        const errorMessages = {
            user: "Problème de connexion, vérifiez votre réseau",
            dev: `Network or parsing error: ${error.message}`
        }
        console.error("[postLogin]", errorMessages.dev)
        return { success: false, error: errorMessages }
    }
}