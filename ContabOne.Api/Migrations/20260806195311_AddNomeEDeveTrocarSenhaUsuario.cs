using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <inheritdoc />
    public partial class AddNomeEDeveTrocarSenhaUsuario : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "DeveTrocarSenha",
                table: "AspNetUsers",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<string>(
                name: "Nome",
                table: "AspNetUsers",
                type: "text",
                nullable: false,
                defaultValue: "");

            // Antes desta migration o nome de exibição era guardado em UserName
            // (o login devolvia Nome = user.UserName). Sem o backfill, todo
            // usuário já existente apareceria sem nome no painel.
            migrationBuilder.Sql("""
                UPDATE "AspNetUsers" SET "Nome" = "UserName" WHERE "Nome" = '';
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "DeveTrocarSenha",
                table: "AspNetUsers");

            migrationBuilder.DropColumn(
                name: "Nome",
                table: "AspNetUsers");
        }
    }
}
