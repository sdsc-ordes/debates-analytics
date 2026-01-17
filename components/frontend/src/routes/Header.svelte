<script lang="ts">
    import { page } from '$app/state';
    import { auth } from "$lib/auth";
    import { Menu, X } from 'lucide-svelte';

    let homePath = $derived(auth.canEdit ? '/' : '/');
    let mobileMenuOpen = $state(false);

    function toggleMenu() {
        mobileMenuOpen = !mobileMenuOpen;
    }

    function closeMenu() {
        mobileMenuOpen = false;
    }
</script>

<header>
    <div class="header-container">
        <a href={homePath} class="brand">
            <span class="brand-name">Debates</span>
            <span class="brand-mode">{auth.canEdit ? 'Editor' : 'Reader'}</span>
        </a>

        <button class="mobile-toggle" onclick={toggleMenu} aria-label="Toggle menu">
            {#if mobileMenuOpen}
                <X size={24} />
            {:else}
                <Menu size={24} />
            {/if}
        </button>

        <nav class:open={mobileMenuOpen}>
            <ul>
                <li>
                    <a
                        href={homePath}
                        class:active={page.url.pathname === homePath}
                        onclick={closeMenu}
                    >
                        Home
                    </a>
                </li>

                <li>
                    <a
                        href="/search"
                        class:active={page.url.pathname === '/search'}
                        onclick={closeMenu}
                    >
                        Search
                    </a>
                </li>

                {#if auth.canEdit}
                    <li>
                        <a
                            href="/dashboard"
                            class:active={page.url.pathname === '/dashboard'}
                            onclick={closeMenu}
                        >
                            Dashboard
                        </a>
                    </li>
                    <li class="logout-item">
                        <form method="POST" action="/dev/login?/logout">
                            <button type="submit" class="nav-link">Logout</button>
                        </form>
                    </li>
                {/if}
            </ul>
        </nav>
    </div>
</header>

<style>
    header {
        background: white;
        border-bottom: 1px solid var(--border-color);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .header-container {
        max-width: 80rem;
        margin: 0 auto;
        padding: 0 1rem;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
    }

    .brand:hover .brand-name {
        color: var(--primary-color);
    }

    .brand-name {
        font-size: 20px;
        font-weight: 700;
        color: var(--primary-dark-color);
        letter-spacing: -0.02em;
        transition: color 0.15s;
    }

    .brand-mode {
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: white;
        padding: 3px 8px;
        background: var(--primary-color);
        border-radius: 4px;
    }

    .mobile-toggle {
        display: none;
        background: none;
        border: none;
        padding: 8px;
        cursor: pointer;
        color: var(--primary-dark-color);
        transition: color 0.15s;
    }

    .mobile-toggle:hover {
        color: var(--secondary-color);
    }

    nav ul {
        display: flex;
        align-items: center;
        gap: 4px;
        list-style: none;
        margin: 0;
        padding: 0;
    }

    nav a,
    .nav-link {
        display: block;
        padding: 8px 14px;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-muted);
        text-decoration: none;
        border-radius: 6px;
        transition: color 0.15s, background-color 0.15s;
        background: none;
        border: none;
        cursor: pointer;
        font-family: inherit;
        position: relative;
    }

    nav a:hover,
    .nav-link:hover {
        color: var(--secondary-color);
        background: rgba(255, 85, 0, 0.06);
    }

    nav a.active {
        color: var(--primary-dark-color);
        font-weight: 600;
    }

    nav a.active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 14px;
        right: 14px;
        height: 2px;
        background: var(--secondary-color);
        border-radius: 1px;
    }

    .logout-item {
        margin-left: 8px;
        padding-left: 12px;
        border-left: 1px solid var(--border-color);
    }

    .logout-item .nav-link {
        color: var(--text-light);
    }

    .logout-item .nav-link:hover {
        color: var(--secondary-dark-color);
        background: rgba(255, 85, 0, 0.06);
    }

    form {
        margin: 0;
    }

    /* Mobile styles */
    @media (max-width: 640px) {
        .mobile-toggle {
            display: block;
        }

        nav {
            position: absolute;
            top: 56px;
            left: 0;
            right: 0;
            background: white;
            border-bottom: 1px solid var(--border-color);
            padding: 8px 1rem 16px;
            display: none;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        nav.open {
            display: block;
        }

        nav ul {
            flex-direction: column;
            align-items: stretch;
            gap: 2px;
        }

        nav a,
        .nav-link {
            padding: 12px 14px;
            width: 100%;
            text-align: left;
        }

        nav a.active::after {
            left: 0;
            right: auto;
            top: 12px;
            bottom: 12px;
            width: 3px;
            height: auto;
        }

        .logout-item {
            margin-left: 0;
            padding-left: 0;
            border-left: none;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--border-color);
        }
    }
</style>
