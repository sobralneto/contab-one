using System.Security.Claims;
using System.Text;
using System.Threading.RateLimiting;
using FluentValidation;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using ContabOne.Api.Domain;
using ContabOne.Api.Features.Admin;
using ContabOne.Api.Features.Produtos;
using ContabOne.Api.Features.Agent;
using ContabOne.Api.Features.Alertas;
using ContabOne.Api.Features.Auth;
using ContabOne.Api.Features.Clientes;
using ContabOne.Api.Features.Dashboard;
using ContabOne.Api.Features.Pgdas;
using ContabOne.Api.Features.Seed;
using ContabOne.Api.Features.Tour;
using ContabOne.Api.Features.Usuarios;
using ContabOne.Api.Infra;
using ContabOne.Api.Jobs;
using Scalar.AspNetCore;
using Serilog;

Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .WriteTo.Console()
    .CreateLogger();

// ── Cron mode: dotnet ContabOne.Api.dll --job=alertas ──
if (args.Any(a => a.StartsWith("--job=")))
{
    var exitCode = await CronRunner.RunAsync(args);
    await Log.CloseAndFlushAsync();
    Environment.Exit(exitCode);
}

try
{
    var builder = WebApplication.CreateBuilder(args);

    builder.Host.UseSerilog((ctx, lc) => lc
        .ReadFrom.Configuration(ctx.Configuration)
        .WriteTo.Console());

    // ── Database ──
    var rawConnString = builder.Configuration.GetValue<string>("DATABASE_URL")
                        ?? builder.Configuration.GetConnectionString("Default")
                        ?? throw new InvalidOperationException("DATABASE_URL or ConnectionStrings:Default is required");

    var connString = DatabaseUrlConverter.ToConnectionString(rawConnString);

    builder.Services.AddDbContext<AppDbContext>(opts =>
        opts.UseNpgsql(connString,
            npgsql => npgsql.EnableRetryOnFailure(3)));

    // ── Identity ──
    builder.Services.AddIdentityCore<Usuario>(opts =>
    {
        opts.Password.RequireDigit = true;
        opts.Password.RequireLowercase = true;
        opts.Password.RequireUppercase = true;
        opts.Password.RequireNonAlphanumeric = false;
        opts.Password.RequiredLength = 8;
        opts.User.RequireUniqueEmail = true;
        opts.SignIn.RequireConfirmedAccount = false;
        // Lockout explícito — não herda o padrão implícito do Identity (§7.2)
        opts.Lockout.AllowedForNewUsers = true;
        opts.Lockout.MaxFailedAccessAttempts = 5;
        opts.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(5);
    })
    .AddRoles<IdentityRole<Guid>>()
    .AddEntityFrameworkStores<AppDbContext>()
    .AddDefaultTokenProviders();

    // ── FluentValidation ──
    builder.Services.AddValidatorsFromAssemblyContaining<ClienteRequestValidator>();

    // ── Tenant context — scoped to request (§5 item 2) ──
    builder.Services.AddScoped<TenantContext>();

    // ── Auth: JWT (humans) + API Key (agents) ──
    var jwtKey = builder.Configuration["JWT_SIGNING_KEY"]
                 ?? throw new InvalidOperationException("JWT_SIGNING_KEY env var is required");

    // HMAC_CNPJ_KEY é permanente: trocá-la invalida todos os CnpjHash já gravados
    // e duplica os clientes. Sem ela o handshake entrega hmacCnpjKey vazio e o
    // agente silenciosamente deixa de enviar o relatório de métricas inteiro.
    // O valor é lido de novo no handshake (config["HMAC_CNPJ_KEY"]); aqui só se
    // garante que a variável existe antes de subir.
    _ = builder.Configuration["HMAC_CNPJ_KEY"]
        ?? throw new InvalidOperationException("HMAC_CNPJ_KEY env var is required");

    builder.Services.AddAuthentication(opts =>
    {
        opts.DefaultAuthenticateScheme = "JwtOrApiKey";
        opts.DefaultChallengeScheme = "JwtOrApiKey";
        opts.DefaultScheme = "JwtOrApiKey";
    })
    .AddJwtBearer(opts =>
    {
        // Mesmas constantes que AuthEndpoints usa para emitir — os dois lados
        // têm que ler a mesma configuração, senão a API rejeita os próprios
        // tokens no instante em que JWT_ISSUER for definido no ambiente.
        var issuer = builder.Configuration["JWT_ISSUER"] ?? AuthEndpoints.IssuerPadrao;
        var audience = builder.Configuration["JWT_AUDIENCE"] ?? AuthEndpoints.AudiencePadrao;
        opts.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidIssuer = issuer,
            ValidAudience = audience,
            ValidateIssuer = true,
            ValidateAudience = true,
            ClockSkew = TimeSpan.FromMinutes(1),
            ValidateLifetime = true,
        };
    })
    .AddPolicyScheme("JwtOrApiKey", "JWT or API Key", opts =>
    {
        opts.ForwardDefaultSelector = ctx =>
        {
            if (ctx.Request.Headers.ContainsKey("X-Api-Key"))
                return "ApiKey";
            return JwtBearerDefaults.AuthenticationScheme;
        };
    })
    .AddScheme<Microsoft.AspNetCore.Authentication.AuthenticationSchemeOptions, ApiKeyAuthenticationHandler>(
        "ApiKey", null);

    builder.Services.AddAuthorization(opts =>
    {
        opts.AddPolicy("Agente", p => p.RequireRole("Agente"));
        opts.AddPolicy("PlatformAdmin", p => p.RequireRole("PlatformAdmin"));
        opts.AddPolicy("EscritorioAdmin", p => p.RequireRole("EscritorioAdmin", "PlatformAdmin"));
        opts.AddPolicy("EscritorioUsuario", p => p.RequireRole("EscritorioUsuario", "EscritorioAdmin", "PlatformAdmin"));
    });

    // ── CORS ──
    var isDevelopment = builder.Environment.IsDevelopment();
    builder.Services.AddCors(opts =>
    {
        opts.AddDefaultPolicy(policy =>
        {
            if (isDevelopment)
            {
                // Dev: allow any localhost port (Vite picks random ports)
                policy.SetIsOriginAllowed(origin => new Uri(origin).Host == "localhost")
                      .AllowAnyHeader()
                      .AllowAnyMethod()
                      .AllowCredentials();
            }
            else
            {
                var corsOrigins = builder.Configuration["CORS_ORIGINS"] ?? "";
                policy.WithOrigins(corsOrigins.Split(',', StringSplitOptions.RemoveEmptyEntries))
                      .AllowAnyHeader()
                      .AllowAnyMethod()
                      .AllowCredentials();
            }
        });
    });

    // ── JSON serialization (required for list parameters from agent) ──
    builder.Services.ConfigureHttpJsonOptions(opts =>
    {
        opts.SerializerOptions.PropertyNameCaseInsensitive = true;
        opts.SerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });

    // ── Rate limiting — particionado por IP, senão o limite é um balde global
    // compartilhado por todos os clientes (ver RateLimitPartition) ──
    builder.Services.AddRateLimiter(opts =>
    {
        // Default do ASP.NET Core é 503 (Service Unavailable), que parece o serviço
        // caído. 429 é o status correto para "excedeu o limite, tente de novo".
        opts.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
        opts.OnRejected = (context, ct) =>
        {
            context.HttpContext.Response.Headers.RetryAfter = "60";
            return ValueTask.CompletedTask;
        };

        opts.AddPolicy("auth", httpContext =>
            RateLimitPartition.GetFixedWindowLimiter(
                partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
                factory: _ => new FixedWindowRateLimiterOptions
                {
                    PermitLimit = 10,
                    Window = TimeSpan.FromMinutes(1),
                    QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                    QueueLimit = 2,
                }));
        opts.AddPolicy("agent", httpContext =>
            RateLimitPartition.GetFixedWindowLimiter(
                partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
                factory: _ => new FixedWindowRateLimiterOptions
                {
                    PermitLimit = 60,
                    Window = TimeSpan.FromMinutes(1),
                    QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                    QueueLimit = 5,
                }));
    });

    // ── OpenAPI + Scalar ──
    builder.Services.AddOpenApi();

    // ── Respostas de erro consistentes para exceções não tratadas ──
    builder.Services.AddProblemDetails();

    var app = builder.Build();

    // ── Run migrations on startup ──
    using (var scope = app.Services.CreateScope())
    {
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        await db.Database.MigrateAsync();
    }

    // ── Forwarded headers — from proxy (Railway/Cloudflare), before rate limiter (§D7) ──
    app.UseForwardedHeaders(new ForwardedHeadersOptions
    {
        ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto,
        // KnownProxies/KnownNetworks configured via config (see design D7, Open Q1)
    });

    // ── Pipeline ──
    app.UseExceptionHandler(eh => eh.Run(async ctx =>
    {
        ctx.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await Results.Problem(statusCode: StatusCodes.Status500InternalServerError)
            .ExecuteAsync(ctx);
    }));
    app.UseSerilogRequestLogging();

    // ── Security headers ──
    if (!app.Environment.IsDevelopment())
    {
        app.UseHsts();
    }

    app.Use(async (ctx, next) =>
    {
        ctx.Response.Headers.Append("X-Frame-Options", "DENY");
        ctx.Response.Headers.Append("X-Content-Type-Options", "nosniff");
        ctx.Response.Headers.Append("Referrer-Policy", "strict-origin-when-cross-origin");
        ctx.Response.Headers.Append("Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), interest-cohort=()");
        await next();
    });

    app.UseCors();
    app.UseRateLimiter();
    app.UseAuthentication();
    app.UseMiddleware<TenantContextMiddleware>(); // populate TenantContext from JWT claims (§5)
    app.UseAuthorization();

    // ── Health ──
    app.MapGet("/health", () => Results.Ok(new { status = "ok", timestamp = DateTime.UtcNow }))
       .AllowAnonymous();

    // ── Seed + OpenAPI (development only) ──
    if (app.Environment.IsDevelopment())
    {
        app.MapOpenApi();
        app.MapScalarApiReference();
        app.MapSeedEndpoints();
    }

    // ── Auth endpoints ──
    app.MapGroup("/api/auth")
       .MapAuthEndpoints()
       .RequireRateLimiting("auth");

    // ── Agent endpoints ──
    app.MapGroup("/api/agent")
       .MapAgentEndpoints()
       .RequireAuthorization("Agente")
       .RequireRateLimiting("agent");

    // ── Dashboard endpoints ──
    app.MapGroup("/api/dashboard")
       .MapDashboardEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    // ── Cliente endpoints ──
    app.MapGroup("/api/clientes")
       .MapClientesEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    // ── Execução endpoints ──
    app.MapGroup("/api/execucoes")
       .MapExecucoesEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    // ── Alerta endpoints ──
    app.MapGroup("/api/alertas")
       .MapAlertasEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    // ── Config endpoints ──
    app.MapGroup("/api/configuracao")
       .MapConfiguracaoEndpoints()
       .RequireAuthorization("EscritorioAdmin");

    // ── Agente management endpoints ──
    app.MapGroup("/api/agentes")
       .MapAgentesManagementEndpoints()
       .RequireAuthorization("EscritorioAdmin");

    // ── Tour endpoints — qualquer usuário autenticado marca as próprias páginas ──
    app.MapGroup("/api/tour")
       .MapTourEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    // ── Usuário endpoints — a policy admite EscritorioAdmin e PlatformAdmin;
    // a separação entre "meu escritório" e "todos" é feita dentro dos handlers
    // pelo TenantContext (ver UsuariosEndpoints) ──
    app.MapGroup("/api/usuarios")
       .MapUsuariosEndpoints()
       .RequireAuthorization("EscritorioAdmin");

    // ── Admin endpoints ──
    app.MapGroup("/api/produtos")
       .MapProdutosEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    app.MapGroup("/api/admin")
       .MapAdminEndpoints()
       .RequireAuthorization("PlatformAdmin");

    // ── PGDAS-D endpoints — mesma exigência de autenticação humana das
    // demais rotas de painel; ferramenta sem agente, sem grupo /api/agent ──
    app.MapGroup("/api/pgdas")
       .MapPgdasEndpoints()
       .RequireAuthorization("EscritorioUsuario");

    app.Run();
}
// `when (ex is not HostAbortedException)`: o HostFactoryResolver do ASP.NET
// Core interrompe o boot de propósito (lançando HostAbortedException) para
// capturar o IHost construído — é assim que o WebApplicationFactory sobe a
// aplicação em testes in-process. Um catch largo aqui engoliria essa exceção
// e a fábrica falharia com "The entry point exited without ever building an
// IHost". Em produção a HostAbortedException nunca acontece por acidente —
// não limpar este filtro sem entender o teste que depende dele.
catch (Exception ex) when (ex is not HostAbortedException)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    await Log.CloseAndFlushAsync();
}

/// <summary>
/// Expõe o entry point como classe parcial — o padrão documentado para
/// permitir `WebApplicationFactory<Program>` com top-level statements
/// (Microsoft.AspNetCore.Mvc.Testing). Sem isso o tipo Program não é
/// visível para o host de teste.
/// </summary>
public partial class Program { }
