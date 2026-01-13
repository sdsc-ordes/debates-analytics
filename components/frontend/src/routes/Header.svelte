<script lang="ts">
    import { page } from '$app/state';
    import { auth } from "$lib/auth";

    let homePath = $derived(auth.canEdit ? '/' : '/');
</script>

<header>
    <div class="corner">
        <nav>
            <label>
                {auth.canEdit ? 'Editor' : 'Reader'}
            </label>
            <ul>
                <li aria-current={page.url.pathname === homePath ? 'page' : undefined}>
                    <a href={homePath}>Home</a>
                </li>

                <li aria-current={page.url.pathname === '/search' ? 'page' : undefined}>
                    <a href="/search">Search</a>
                </li>

                {#if auth.canEdit}
                    <li aria-current={page.url.pathname === '/dashboard' ? 'page' : undefined}>
                        <a href="/dashboard">Dashboard</a>
                    </li>
                    <li>
                        <form method="POST" action="/dev/login?/logout">
                           <button type="submit" class="link-button">Logout</button>
                        </form>
                    </li>
                {/if}
            </ul>
        </nav>
    </div>
</header>

<style>
	header {
		display: flex;
		justify-content: center;
		align-items: center;
		}

	.corner {
		width: 3em;
		height: 3em;
	}

	nav {
		display: flex;
		justify-content: center;
		--background: rgba(255, 255, 255, 0.7);
	}

	svg {
		width: 2em;
		height: 3em;
		display: block;
	}

	path {
		fill: var(--background);
	}

	ul {
		position: relative;
		padding: 0;
		margin: 0;
		height: 3em;
		display: flex;
		justify-content: center;
		align-items: center;
		list-style: none;
		background: var(--background);
		background-size: contain;
	}

	li {
		position: relative;
		height: 100%;
	}

	li[aria-current='page']::before {
		--size: 6px;
		content: '';
		width: 0;
		height: 0;
		position: absolute;
		top: 0;
		left: calc(50% - var(--size));
		border: var(--size) solid transparent;
		border-top: var(--size) solid var(--secondary-color);
	}

	nav a {
		display: flex;
		height: 100%;
		align-items: center;
		padding: 0 0.5rem;
		color: var(--text-color);
		font-weight: 700;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		text-decoration: none;
		transition: color 0.2s linear;
	}

	nav label {
		position: relative;
		height: 100%;
		display: flex;
		height: 100%;
		align-items: center;
		margin: 15px;
		padding: 0 0.5rem;
		color: var(--text-color);
		font-weight: 700;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		text-decoration: none;
		border-bottom: 3px solid var(--primary-color);
		transition: color 0.2s linear;
	}

	a:hover {
		color: var(--secondary-color);
	}

    form {
        height: 100%;
        display: flex;
    }

    nav a,
    button.link-button {
        display: flex;
        height: 100%;
        align-items: center;
        padding: 0 0.5rem;
        color: var(--text-color);
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        text-decoration: none;
        transition: color 0.2s linear;
        background: none;
        border: none;
        cursor: pointer;
        font-family: inherit;
    }

    nav a:hover,
    button.link-button:hover {
        color: var(--secondary-color);
    }
</style>
