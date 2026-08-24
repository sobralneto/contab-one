using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <summary>
    /// `ConfiguracaoEscritorio` passa a ser por (escritório, ferramenta), não
    /// só por escritório — período de busca, tipos de nota e afins são
    /// próprios de cada ferramenta, e DET não tem por que herdar os ajustes
    /// do NFS-e.
    ///
    /// Mesma disciplina de ordem das migrations anteriores: `ProdutoId` entra
    /// anulável, o backfill atribui toda configuração existente ao NFS-e (a
    /// única ferramenta que tinha Configuração antes desta mudança), e só
    /// então a coluna vira obrigatória e entra na chave primária.
    /// </summary>
    public partial class EscritorioConfigPorFerramenta : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropPrimaryKey(
                name: "PK_ConfiguracoesEscritorio",
                table: "ConfiguracoesEscritorio");

            migrationBuilder.AddColumn<Guid>(
                name: "ProdutoId",
                table: "ConfiguracoesEscritorio",
                type: "uuid",
                nullable: true);

            // Backfill pelo Codigo (estável): toda linha existente é do NFS-e
            // — a única ferramenta que tinha tela de Configuração até aqui.
            migrationBuilder.Sql("""
                UPDATE "ConfiguracoesEscritorio" ce
                SET "ProdutoId" = p."Id"
                FROM "Produtos" p
                WHERE p."Codigo" = 'nfse';
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "ProdutoId",
                table: "ConfiguracoesEscritorio",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddPrimaryKey(
                name: "PK_ConfiguracoesEscritorio",
                table: "ConfiguracoesEscritorio",
                columns: new[] { "EscritorioId", "ProdutoId", "Chave" });

            migrationBuilder.CreateIndex(
                name: "IX_ConfiguracoesEscritorio_ProdutoId",
                table: "ConfiguracoesEscritorio",
                column: "ProdutoId");

            migrationBuilder.AddForeignKey(
                name: "FK_ConfiguracoesEscritorio_Produtos_ProdutoId",
                table: "ConfiguracoesEscritorio",
                column: "ProdutoId",
                principalTable: "Produtos",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_ConfiguracoesEscritorio_Produtos_ProdutoId",
                table: "ConfiguracoesEscritorio");

            migrationBuilder.DropPrimaryKey(
                name: "PK_ConfiguracoesEscritorio",
                table: "ConfiguracoesEscritorio");

            migrationBuilder.DropIndex(
                name: "IX_ConfiguracoesEscritorio_ProdutoId",
                table: "ConfiguracoesEscritorio");

            migrationBuilder.DropColumn(
                name: "ProdutoId",
                table: "ConfiguracoesEscritorio");

            migrationBuilder.AddPrimaryKey(
                name: "PK_ConfiguracoesEscritorio",
                table: "ConfiguracoesEscritorio",
                columns: new[] { "EscritorioId", "Chave" });
        }
    }
}
