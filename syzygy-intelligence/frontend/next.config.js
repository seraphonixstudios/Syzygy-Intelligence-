/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    async rewrites() {
        return [
            { source: "/favicon.ico", destination: "/favicon.svg" },
        ];
    },

};

module.exports = nextConfig;
