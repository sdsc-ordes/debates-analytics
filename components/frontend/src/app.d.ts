declare global {
	namespace App {
		interface Locals {
			user: {
				id: string;
				role: 'reader' | 'editor';
			} | null;
		}
		// interface Error {}
		// interface Platform {}
	}
}

export {};
