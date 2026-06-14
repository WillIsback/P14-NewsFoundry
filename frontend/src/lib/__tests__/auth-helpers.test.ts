import { getLoginPayload, validateLoginPayload } from "../auth-helpers";

// `Parameters<typeof fn>[0]` récupère le type exact attendu par la fonction
// sans importer le schéma Zod généré (LoginResponse) directement.
type OkArg = Parameters<typeof getLoginPayload>[0];
type ErrArg = Extract<OkArg, { ok: false }>;

const ok = (data: unknown) =>
	({ ok: true as const, status: 200, data }) as OkArg;

const err: ErrArg = {
	ok: false,
	status: 401,
	error: {
		kind: "http",
		code: "HTTP_401",
		message: "Unauthorized",
		userMessage: "Non autorisé",
	},
};

describe("getLoginPayload", () => {
	it("retourne data.data quand la réponse est ok", () => {
		expect(getLoginPayload(ok({ data: { email: "a@b.com" } }))).toEqual({
			email: "a@b.com",
		});
	});

	it("retourne null quand le résultat est une erreur", () => {
		expect(getLoginPayload(err)).toBeNull();
	});

	it("retourne null quand data.data est absent (undefined)", () => {
		expect(getLoginPayload(ok({}))).toBeNull();
	});
});

describe("validateLoginPayload", () => {
	it("retourne l'email quand il est valide", () => {
		expect(
			validateLoginPayload(ok({ data: { email: "user@example.com" } })),
		).toBe("user@example.com");
	});

	it("retourne null quand l'email est une chaîne vide", () => {
		expect(validateLoginPayload(ok({ data: { email: "" } }))).toBeNull();
	});

	it("retourne null quand le résultat est une erreur", () => {
		expect(validateLoginPayload(err)).toBeNull();
	});
});
