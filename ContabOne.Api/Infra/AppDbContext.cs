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
    public DbSet<Dominio> Dominios => Set<Dominio>();
    public DbSet<Produto> Produtos => Set<Produto>();
    public DbSet<EscritorioProduto> EscritorioProdutos => Set<EscritorioProduto>();
    public DbSet<Agente> Agentes => Set<Agente>();
    public DbSet<Cliente> Clientes => Set<Cliente>();
    public DbSet<Execucao> Execucoes => Set<Execucao>();
    public DbSet<ExecucaoMetrica> ExecucaoMetricas => Set<ExecucaoMetrica>();
    public DbSet<RegraColeta> RegraColetas => Set<RegraColeta>();
    public DbSet<ConfiguracaoEscritorio> ConfiguracoesEscritorio => Set<ConfiguracaoEscritorio>();
    public DbSet<Alerta> Alertas => Set<Alerta>();
    public DbSet<TourPaginaVista> TourPaginasVistas => Set<TourPaginaVista>();
    public DbSet<ApuracaoSimples> ApuracoesSimples => Set<ApuracaoSimples>();
    public DbSet<ApuracaoSegregacao> ApuracaoSegregacoes => Set<ApuracaoSegregacao>();
    public DbSet<ReceitaMensalCliente> ReceitasMensaisCliente => Set<ReceitaMensalCliente>();

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

        modelBuilder.Entity<EscritorioProduto>().HasQueryFilter(ep =>
            _tenantContext.VeTodosOsEscritorios || ep.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<ApuracaoSimples>().HasQueryFilter(a =>
            _tenantContext.VeTodosOsEscritorios || a.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<ApuracaoSegregacao>().HasQueryFilter(s =>
            _tenantContext.VeTodosOsEscritorios || s.Apuracao.EscritorioId == _tenantContext.EscritorioId);

        modelBuilder.Entity<ReceitaMensalCliente>().HasQueryFilter(r =>
            _tenantContext.VeTodosOsEscritorios || r.EscritorioId == _tenantContext.EscritorioId);

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

        modelBuilder.Entity<Dominio>(e =>
        {
            e.HasKey(x => x.Codigo);
        });

        modelBuilder.Entity<Produto>(e =>
        {
            e.HasKey(x => x.Id);
            // Catálogo global do hub: sem query filter de tenant de propósito
            // — todo escritório enxerga as mesmas ferramentas.
            e.HasIndex(x => x.Codigo).IsUnique();
            e.HasOne(x => x.Dominio).WithMany(d => d.Produtos)
                .HasForeignKey(x => x.DominioCodigo).OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<EscritorioProduto>(e =>
        {
            // Chave composta: um escritorio tem no maximo uma linha por
            // produto. Reabilitar limpa DesabilitadoEm em vez de criar linha
            // nova, entao o historico nao vira duplicata.
            e.HasKey(x => new { x.EscritorioId, x.ProdutoId });
            e.HasOne(x => x.Escritorio).WithMany(es => es.Produtos)
                .HasForeignKey(x => x.EscritorioId).OnDelete(DeleteBehavior.Cascade);
            e.HasOne(x => x.Produto).WithMany(pr => pr.Escritorios)
                .HasForeignKey(x => x.ProdutoId).OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<Agente>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasOne(x => x.Escritorio).WithMany(es => es.Agentes).HasForeignKey(x => x.EscritorioId);
            // Restrict: apagar um produto com agente em campo invalidaria as
            // chaves que estão nos config.toml dos clientes.
            e.HasOne(x => x.Produto).WithMany(pr => pr.Agentes)
                .HasForeignKey(x => x.ProdutoId).OnDelete(DeleteBehavior.Restrict);
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
            e.HasKey(x => new { x.EscritorioId, x.ProdutoId, x.Chave });
            e.HasOne(x => x.Escritorio).WithMany(es => es.Configuracoes).HasForeignKey(x => x.EscritorioId);
            e.HasOne(x => x.Produto).WithMany().HasForeignKey(x => x.ProdutoId).OnDelete(DeleteBehavior.Restrict);
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

        modelBuilder.Entity<ApuracaoSimples>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasIndex(x => new { x.EscritorioId, x.ClienteId, x.Competencia }).IsUnique();
            e.HasOne(x => x.Escritorio).WithMany().HasForeignKey(x => x.EscritorioId);
            e.HasOne(x => x.Cliente).WithMany().HasForeignKey(x => x.ClienteId);

            e.Property(x => x.Faturamento).HasColumnType("numeric(18,2)");
            e.Property(x => x.Das).HasColumnType("numeric(18,2)");
            e.Property(x => x.Irpj).HasColumnType("numeric(18,2)");
            e.Property(x => x.Csll).HasColumnType("numeric(18,2)");
            e.Property(x => x.Cofins).HasColumnType("numeric(18,2)");
            e.Property(x => x.Pis).HasColumnType("numeric(18,2)");
            e.Property(x => x.Inss).HasColumnType("numeric(18,2)");
            e.Property(x => x.Icms).HasColumnType("numeric(18,2)");
            e.Property(x => x.Ipi).HasColumnType("numeric(18,2)");
            e.Property(x => x.Iss).HasColumnType("numeric(18,2)");
            e.Property(x => x.Rba).HasColumnType("numeric(18,2)");
            e.Property(x => x.Sublimite).HasColumnType("numeric(18,2)");
        });

        modelBuilder.Entity<ApuracaoSegregacao>(e =>
        {
            e.HasKey(x => new { x.ApuracaoId, x.Categoria });
            e.Property(x => x.Receita).HasColumnType("numeric(18,2)");
            // Cascade: a segregação é da apuração daquele mês, sem vida própria.
            e.HasOne(x => x.Apuracao).WithMany(a => a.Segregacoes)
             .HasForeignKey(x => x.ApuracaoId).OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<ReceitaMensalCliente>(e =>
        {
            e.HasKey(x => new { x.EscritorioId, x.ClienteId, x.Competencia });
            e.Property(x => x.ReceitaBruta).HasColumnType("numeric(18,2)");
            e.HasOne(x => x.Escritorio).WithMany().HasForeignKey(x => x.EscritorioId);
            e.HasOne(x => x.Cliente).WithMany().HasForeignKey(x => x.ClienteId);
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
