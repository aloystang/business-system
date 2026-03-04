# Linear Setup For Home-Hosted Launch

Use Linear for coordination, not for hosting. A good first project is `Home Hosted Launch`.

## Suggested Project Structure

- Team: whichever team owns the product and deployment work
- Project: `Home Hosted Launch`
- Status buckets:
  - Todo
  - In Progress
  - In Review
  - Deployed To Vercel
  - Deployed To Spare Mac
  - Monitoring

## Suggested Issues

1. Buy domain and move DNS to Cloudflare
2. Create Vercel project for `frontend`
3. Configure `app.yourdomain.com` on Vercel
4. Install `cloudflared` on the spare Mac
5. Create named tunnel for `api.yourdomain.com`
6. Rotate `JWT_SECRET` and admin credentials
7. Configure backend `.env` on the spare Mac
8. Configure `folo-bridge/.env` on the spare Mac
9. Install launchd agents for backend, bridge, sync, cloudflared, and backup
10. Test deploy flow from Git on the spare Mac
11. Verify public login and key pages
12. Run 7-day stability watch

## Recommended Labels

- infra
- frontend
- backend
- intel
- launchd
- cloudflare
- vercel
- backup
- security

## What Linear Helps With

- Splitting the launch into trackable issues
- Recording failures like tunnel drops or sync jobs that stop running
- Tracking whether a change is deployed only to Vercel or also to the spare Mac
- Linking GitHub pull requests to the deployment work

## What Linear Does Not Replace

- Vercel
- Cloudflare Tunnel
- launchd
- backups
- runtime monitoring
