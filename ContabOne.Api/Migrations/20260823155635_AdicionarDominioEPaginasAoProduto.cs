using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <summary>
    /// O catálogo de ferramentas ganha domínio (departamento do escritório
    /// contábil que a ferramenta atende) e as páginas que cada uma declara
    /// ter — a base de dado que o frontend passa a usar para agrupar o menu
    /// e montar o submenu de cada ferramenta, em vez de tê-los escritos no
    /// template.
    ///
    /// Mesma disciplina de ordem de <see cref="ProdutosComoTabela"/>: as
    /// colunas novas entram anuláveis, o backfill roda pelo `Codigo` (estável,
    /// ao contrário do Id que varia por ambiente), e só então viram
    /// obrigatórias — sem janela em que produto existente fique inválido.
    /// </summary>
    public partial class AdicionarDominioEPaginasAoProduto : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Dominios",
                columns: table => new
                {
                    Codigo = table.Column<string>(type: "text", nullable: false),
                    Nome = table.Column<string>(type: "text", nullable: false),
                    Ordem = table.Column<int>(type: "integer", nullable: false),
                    Icone = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Dominios", x => x.Codigo);
                });

            // Seed dos três domínios. "DP", não "Departamento Pessoal": é como
            // o escritório contábil chama o departamento, e cabe no menu
            // recolhido sem precisar de uma coluna de nome curto separada.
            migrationBuilder.Sql("""
                INSERT INTO "Dominios" ("Codigo", "Nome", "Ordem", "Icone")
                VALUES
                    ('fiscal', 'Fiscal', 1, 'file-invoice'),
                    ('dp', 'DP', 2, 'mailbox'),
                    ('contabil', 'Contábil', 3, 'calculator');
                """);

            // Nullable primeiro: sem valor ainda para os produtos existentes.
            migrationBuilder.AddColumn<string>(
                name: "DominioCodigo",
                table: "Produtos",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<string[]>(
                name: "Paginas",
                table: "Produtos",
                type: "text[]",
                nullable: true);

            // Backfill pelo Codigo (estável entre ambientes, ao contrário do
            // Id). Clientes e Agentes NÃO entram em Paginas: as duas telas
            // mostram dado do escritório inteiro, não particionado por
            // produto no banco — vivem em rotas transversais, fora de
            // /f/:produto/. Regras só o NFS-e declara — é o cadastro do
            // pacote que os agentes baixam para conversar com o Portal
            // Nacional, sem equivalente em outra ferramenta ainda.
            migrationBuilder.Sql("""
                UPDATE "Produtos" SET
                    "DominioCodigo" = 'fiscal',
                    "Paginas" = ARRAY['visao-geral','execucoes','configuracao','regras']
                WHERE "Codigo" = 'nfse';

                UPDATE "Produtos" SET
                    "DominioCodigo" = 'dp',
                    "Paginas" = ARRAY['visao-geral','execucoes']
                WHERE "Codigo" = 'det';
                """);

            // Rede de segurança: produto cadastrado depois de ProdutosComoTabela
            // e antes desta migration (nenhum conhecido hoje, mas o mesmo
            // cuidado da migration anterior) cai em Fiscal com a página
            // mínima, para não travar o ALTER abaixo.
            migrationBuilder.Sql("""
                UPDATE "Produtos" SET "DominioCodigo" = 'fiscal' WHERE "DominioCodigo" IS NULL;
                UPDATE "Produtos" SET "Paginas" = ARRAY['visao-geral'] WHERE "Paginas" IS NULL;
                """);

            migrationBuilder.AlterColumn<string>(
                name: "DominioCodigo",
                table: "Produtos",
                type: "text",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "text",
                oldNullable: true);

            migrationBuilder.AlterColumn<string[]>(
                name: "Paginas",
                table: "Produtos",
                type: "text[]",
                nullable: false,
                oldClrType: typeof(string[]),
                oldType: "text[]",
                oldNullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_Produtos_DominioCodigo",
                table: "Produtos",
                column: "DominioCodigo");

            migrationBuilder.AddForeignKey(
                name: "FK_Produtos_Dominios_DominioCodigo",
                table: "Produtos",
                column: "DominioCodigo",
                principalTable: "Dominios",
                principalColumn: "Codigo",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Produtos_Dominios_DominioCodigo",
                table: "Produtos");

            migrationBuilder.DropTable(
                name: "Dominios");

            migrationBuilder.DropIndex(
                name: "IX_Produtos_DominioCodigo",
                table: "Produtos");

            migrationBuilder.DropColumn(
                name: "DominioCodigo",
                table: "Produtos");

            migrationBuilder.DropColumn(
                name: "Paginas",
                table: "Produtos");
        }
    }
}
