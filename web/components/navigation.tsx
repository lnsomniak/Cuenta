// new navigation component, just linking my browse page that I integrated last night and the main page.
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navigation() {
    const pathname = usePathname();

    const links = [
        { href: "/", label: "OPTIMIZE" },
        { href: "/browse", label: "BROWSE" },
    ];

    return (
        <nav
            className="w-full max-w-md mx-auto mb-4"
            style={{ fontFamily: "'Courier New', Courier, monospace" }}
        >
            <div className="flex border-2 border-gray-700 overflow-hidden">
                {links.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            className="flex-1 py-2 text-center text-xs tracking-widest transition-colors"
                            style={{
                                backgroundColor: isActive ? "#1a1a1a" : "#fefefa",
                                color: isActive ? "#fefefa" : "#1a1a1a",
                            }}
                        >
                            {link.label}
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}