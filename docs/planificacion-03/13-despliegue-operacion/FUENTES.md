# Fuentes primarias y extractos — despliegue/operación

Consulta documental: 2026-10-26. Los extractos se conservan en inglés tal como aparecen en las páginas oficiales; las recomendaciones de `ESPECIFICACION.md` son propuestas operativas, no certificaciones de que el proyecto esté desplegado o probado. IDs corresponden al ledger propio `sources-ledger.json`.

## Extractos relevantes

1. PostgreSQL, capítulo de roles — [1]  
   > PostgreSQL manages database access permissions using the concept of roles. A role can be thought of as either a database user, or a group of database users, depending on how the role is set up.

2. PostgreSQL `pg_dump` — [2]  
   > pg_dump is a utility for exporting a PostgreSQL database. It makes consistent exports even if the database is being used concurrently.

3. PostgreSQL `pg_restore` — [3]  
   > Restoring a dump causes the destination to execute arbitrary code of the source superusers' choice.

4. PostgreSQL respaldo/restore SQL — [4]  
   > The basic usage of this command is: `pg_dump dbname > dumpfile`

5. GitHub Actions, mínimo privilegio — [5]  
   > Any user with write access to your repository has read access to all secrets configured in your repository.

6. GitHub Actions, secretos y forks — [6]  
   > secrets are not passed to the runner when a workflow is triggered from a forked repository.

7. GitHub Actions, eventos programados — [7]  
   > You can configure your workflows to run when specific activity on GitHub happens, at a scheduled time, or when an event outside of GitHub occurs.

8. GitHub Environments — [8]  
   > A job that references an environment must follow any protection rules for the environment before running or accessing the environment's secrets.

9. GitHub, licencia — [9]  
   > The Open Source Guide provides additional guidance on choosing the correct license for your project.

10. Cloudflare Pages, rollback — [10]  
    > Any production deployment that has been successfully built is a valid rollback target.

11. Cloudflare Worker Secrets — [11]  
    > Secrets are a type of binding that allow you to attach encrypted text values to your Worker.

12. Cloudflare Workers, cuota Free — [12]  
    > | Requests | 100,000/day | No limit |

13. Cloudflare Workers AI, cuota Free — [13]  
    > Our free allocation allows anyone to use a total of 10,000 Neurons per day at no charge.

14. Neon, scale-to-zero — [14]  
    > For example, if scale to zero is enabled, your compute will transition to an idle state after it's been inactive for 5 minutes.

15. Neon, cold start — [15]  
    > Currently, activating a Neon compute from an idle state typically takes a few hundred milliseconds not counting other factors that can add to latencies such as the physical distance between your application and database or startup times of other services that participate in your connection process.

16. Neon, producción — [16]  
    > The Free plan is designed to support experimentation and prototyping and includes compute hour limits. It should be avoided for production workloads where uninterrupted availability matters.

17. Supabase, pausa Free — [17]  
    > Supabase pauses Free Plan projects that show low activity over a 7-day period to save server resources.

18. Supabase, backups — [18]  
    > We recommend that free tier plan projects regularly export their data using the Supabase CLI `db dump` command and maintain off-site backups.

19. PostgreSQL, configuración de roles — [19]  
    > Since the role identity determines the set of privileges available to a connected client, it is important to carefully configure privileges when setting up a multiuser environment.

20. PostgreSQL, privilegios — [20]  
    > For details see the GRANT and REVOKE reference pages.

21. Cloudflare Pages, previews — [21]  
    > When a preview deployment is published, it is given a unique, hash-based address — for example, `<hash>.<project>.pages.dev`.

22. Cloudflare Pages, builds — [22]  
    > Each time you push new code to your Git repository, Pages will build and deploy your site.

23. Vercel Hobby — [23]  
    > The Hobby plan is free and aimed at developers with personal projects, and small-scale applications.

24. Vercel, fair use — [24]  
    > Hobby teams are restricted to non-commercial personal use only.

25. Cloudflare Workers, precio Paid — [25]  
    > The Workers Paid plan includes Workers, Pages Functions, Workers KV, Hyperdrive, and Durable Objects usage for a minimum charge of $5 USD per month for an account.

26. GitHub Actions, retraso de cron — [26]  
    > Scheduled events can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour. If the load is sufficiently high enough, some queued jobs may be dropped.

## Lectura aplicada al plan

- Las cuotas y condiciones Free descritas por un proveedor son límites documentales; no son una prueba de la aplicación Paideia ni una garantía de concurrencia/disponibilidad.
- Neon y Supabase solo aparecen como condiciones a revisar si el equipo/agente API los selecciona. Esta entrega no elige DB ni proveedor LLM.
- `pg_dump`/`psql` se documentan como referencias para un ensayo de exportación/restauración; no se ejecutaron ni se presentan como backup productivo suficiente.
- El cron de ingesta se trata como best-effort; el catálogo retiene un último snapshot validado y se monitoriza su antigüedad.

## Sources

[1] https://www.postgresql.org/docs/current/user-manag.html
[2] https://www.postgresql.org/docs/current/app-pgdump.html
[3] https://www.postgresql.org/docs/current/app-pgrestore.html
[4] https://www.postgresql.org/docs/current/backup-dump.html
[5] https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
[6] https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
[7] https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[8] https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
[9] https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
[10] https://developers.cloudflare.com/pages/configuration/rollbacks
[11] https://developers.cloudflare.com/workers/configuration/secrets
[12] https://developers.cloudflare.com/workers/platform/limits
[13] https://developers.cloudflare.com/workers-ai/platform/pricing
[14] https://neon.tech/docs/guides/scale-to-zero-guide
[15] https://neon.tech/docs/connect/connection-latency
[16] https://neon.tech/docs/get-started-with-neon/production-checklist
[17] https://supabase.com/docs/guides/platform/free-project-pausing
[18] https://supabase.com/docs/guides/platform/backups
[19] https://www.postgresql.org/docs/current/database-roles.html
[20] https://www.postgresql.org/docs/current/ddl-priv.html
[21] https://developers.cloudflare.com/pages/configuration/preview-deployments
[22] https://developers.cloudflare.com/pages/platform/limits
[23] https://vercel.com/docs/plans/hobby
[24] https://vercel.com/docs/limits/fair-use-guidelines
[25] https://developers.cloudflare.com/workers/platform/pricing
[26] https://docs.github.com/en/actions/how-tos/troubleshoot-workflows
