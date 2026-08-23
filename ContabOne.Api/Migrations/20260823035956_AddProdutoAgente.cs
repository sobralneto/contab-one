using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <summary>
    /// Qual ferramenta do hub cada chave de API habilita.
    ///
    /// `defaultValue: 0` não é cosmético: 0 é Produto.Nfse, e as linhas que já
    /// existem foram todas emitidas com prefixo `nfse_`. É o que faz as chaves
    /// já distribuídas continuarem autenticando depois do deploy — o handler
    /// confere o produto da chave contra esta coluna.
    /// </summary>
    public partial class AddProdutoAgente : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<int>(
                name: "Produto",
                table: "Agentes",
                type: "integer",
                nullable: false,
                defaultValue: 0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Produto",
                table: "Agentes");
        }
    }
}
