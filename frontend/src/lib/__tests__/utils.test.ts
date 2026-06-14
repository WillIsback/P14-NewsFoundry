import { cn } from "../utils";

describe("cn", () => {
	it("concatène des classes simples", () => {
		expect(cn("foo", "bar")).toBe("foo bar");
	});

	it("résout les conflits Tailwind (la dernière classe gagne)", () => {
		expect(cn("p-4", "p-2")).toBe("p-2");
	});

	it("ignore les valeurs falsy", () => {
		expect(cn("foo", false, undefined, null, "bar")).toBe("foo bar");
	});
});
