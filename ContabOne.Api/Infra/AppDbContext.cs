using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using ContabOne.Api.Domain;

namespace ContabOne.Api.Infra;

public class AppDbContext : IdentityDbContext<Usuario, IdentityRole<Guid>, Guid>
{
    private readonly TenantContext _tenantContext;

    public AppDbContext(DbContextOptions<AppDbContext> options, TenantContext tenantContext)
        : base(options)
    {
        _tenantContext = tenantContext;
    }

    public DbSet<Escritorio> Escritorios => Set<Escritorio>();
    public DbSet<Plano> Planos => Set<Plano>();
    public DbSet<Agente> Agentes => Set<Agente>();
    public DbSet<Cliente> Clientes => Set<Cliente>();
    public DbSet<Execucao> Execucoes => Set<Execucao>();
    public DbSet<ExecucaoMetrica> ExecucaoMetricas => Set<ExecucaoMetrica>();
    public DbSet<RegraColeta> RegraColetas => Set<RegraColeta>();
    public DbSet<ConfiguracaoEscritorio> ConfiguracoesEscritorio => Set<ConfiguracaoEscritorio>();
    public DbSet<Alerta> Alertas => Set<Alerta>();
    public DbSet<TourPaginaVista> TourPaginasVistas => Set<TourPaginaVista>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── Identity: remove tabelas não utilizadas pelo sistema ──
        // O sistema não usa login externo (Google/Facebook/etc.) nem claims
        // armazenadas no banco (a autorização é feita por roles + JWT claims
        // inline, sem consulta a AspNetUserClaims/AspNetRoleClaims).

        modelBuilder.Ignore<IdentityUserClaim<Guid>>();
        modelBuilder.Ignore<IdentityRoleClaim<Guid>>();
        modelBuilder.Ignore<IdentityUserLogin<Guid>>();

        // ── Global query filters for multi-tenant isolation (§5) ──
        // Fail-closed: VeTodosOsEscritorios (só ligado por FromAdmin) é o
        // único caminho para ver todos os escritórios. EscritorioId nulo sem
        // VeTodosOsEscritorios → nenhuma linha visível (o estado do bug).

        modelBuilder.Entity<Agente>().HasQueryFilter(a =>
            _tenantContext.VeTodosOsEscritorios || a.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<Cliente>().HasQueryFilter(c =>
            _tenantContext.VeTodosOsEscritorios || c.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<Execucao>().HasQueryFilter(e =>
            _tenantContext.VeTodosOsEscritorios || e.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<ExecucaoMetrica>().HasQueryFilter(m =>
            _tenantContext.VeTodosOsEscritorios || m.Execucao.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<ConfiguracaoEscritorio>().HasQueryFilter(c =>
            _tenantContext.VeTodosOsEscritorios || c.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<Alerta>().HasQueryFilter(a =>
            _tenantContext.VeTodosOsEscritorios || a.EscritorioId == _tenantContext.EscritorioId);

        // ── Entity configuration ──

        modelBuilder.Entity<Escritorio>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasIndex(x => x.CnpjHash).IsUnique();
            e.HasOne(x => x.Plano).WithMany(p => p.Escritorios).HasForeignKey(x => x.PlanoId);
        });

        modelBuilder.Entity<Plano>(e =>
        {
            e.HasKey(x => x.Id);
            e.Property(x => x.PrecoMensal).HasColumnType("decimal(10,2)");
        });

        modelBuilder.Entity<Agente>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Escritorio).WithMany(es => es.Agentes).HasForeignKey(x => x.EscritorioId);
        });

        modelBuilder.Entity<Cliente>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Escritorio).WithMany(es => es.Clientes).HasForeignKey(x => x.EscritorioId);
        });

        modelBuilder.Entity<Execucao>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Escritorio).WithMany(es => es.Execucoes).HasForeignKey(x => x.EscritorioId);
            e.HasOne(x => x.Agente).WithMany().HasForeignKey(x => x.AgenteId);
        });

        modelBuilder.Entity<ExecucaoMetrica>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Execucao).WithMany(ex => ex.Metricas).HasForeignKey(x => x.ExecucaoId);
            e.HasOne(x => x.Cliente).WithMany().HasForeignKey(x => x.ClienteId);
        });

        modelBuilder.Entity<RegraColeta>(e =>
        {
            e.HasKey(x => x.Id);
            e.Property(x => x.Conteudo).HasColumnType("jsonb");
            e.HasIndex(x => x.Versao).IsUnique();
        });

        modelBuilder.Entity<ConfiguracaoEscritorio>(e =>
        {
            e.HasKey(x => new { x.EscritorioId, x.Chave });
            e.HasOne(x => x.Escritorio).WithMany(es => es.Configuracoes).HasForeignKey(x => x.EscritorioId);
        });

        modelBuilder.Entity<Alerta>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Escritorio).WithMany(es => es.Alertas).HasForeignKey(x => x.EscritorioId);
            e.HasOne(x => x.Cliente).WithMany().HasForeignKey(x => x.ClienteId);
        });

        modelBuilder.Entity<TourPaginaVista>(e =>
        {
            // Chave composta como em ConfiguracaoEscritorio: a própria chave já
            // impede registrar a mesma página duas vezes para o mesmo usuário.
            e.HasKey(x => new { x.UsuarioId, x.Pagina });
            e.Property(x => x.Pagina).HasMaxLength(60);
            // Cascade: usuário removido não deixa registro de tour órfão.
            e.HasOne(x => x.Usuario).WithMany().HasForeignKey(x => x.UsuarioId)
             .OnDelete(DeleteBehavior.Cascade);
        });

        // ── Indexes that matter from day 1 (§4.2) ──

        modelBuilder.Entity<Execucao>()
            .HasIndex(e => new { e.EscritorioId, e.IniciadoEm }).IsDescending(false, true);

        modelBuilder.Entity<ExecucaoMetrica>()
            .HasIndex(m => m.ExecucaoId);

        modelBuilder.Entity<ExecucaoMetrica>()
            .HasIndex(m => new { m.ClienteId, m.Competencia });

        modelBuilder.Entity<Cliente>()
            .HasIndex(c => new { c.EscritorioId, c.Codigo }).IsUnique();

        modelBuilder.Entity<Agente>()
            .HasIndex(a => a.ApiKeyHash);

        modelBuilder.Entity<Alerta>()
            .HasIndex(a => new { a.EscritorioId, a.ResolvidoEm })
            .HasFilter("\"ResolvidoEm\" IS NULL");
    }
}
