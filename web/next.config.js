/** @type {import('next').NextConfig} */
const nextConfig = {
images: {
    remotePatterns: [
    {
        protocol: 'https',
        hostname: 'spoonacular.com',
    },
    ],
},
}
// none of this is done by me thank you john from accenture.
module.exports = nextConfig