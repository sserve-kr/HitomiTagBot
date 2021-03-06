import discord
from discord.ext.commands import Cog
from discord.commands import SlashCommandGroup
from settings import manage_channel_id, embed_supporter_text
from db import DB_OBJECT

class TagConfirmView(discord.ui.View):
    def __init__(self, ctx, **kwargs):
        super().__init__()
        self.ctx = ctx
        self.args = kwargs
        # tag, desc, prefix, origin, author, bot

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.edit_message(content='DONE')
        sql = "UPDATE Tags SET "
        if self.args['tag']:
            sql += f"korean_name='{self.args['tag']}'"
        if self.args['desc']:
            if self.args['tag']:
                sql += ', '
            desc = self.args['desc'].replace("￦n", "\n")
            sql += f"korean_desc='{desc}'"
        sql += f"WHERE prefix='{self.args['prefix']}' AND tag='{self.args['origin']}'"
        print(sql)
        DB_OBJECT.execute(sql)
        DB_OBJECT.commit()
        await interaction.followup.send(content='Accepted.')

        user = await self.args['bot'].fetch_user(self.args['author'])
        embed = discord.Embed(title='태그 번역/설명이 추가되었습니다.', color=0x32ff32)
        embed.add_field(name="태그 번역", value=str(self.args['tag']))
        embed.add_field(name="태그 설명", value=str(self.args['desc']).replace("￦n", "\n"), inline=False)
        await user.send(embed=embed)
    
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.edit_message(content='DONE.')
        await interaction.followup.send(content='Denied.')

        user = await self.args['bot'].fetch_user(self.args['author'])
        embed = discord.Embed(title='태그 번역/설명이 반려되었습니다.', color=0xff3232)
        embed.add_field(name="태그 번역", value=str(self.args['tag']))
        embed.add_field(name="태그 설명", value=str(self.args['desc']).replace("￦n", "\n"), inline=False)
        await user.send(embed=embed)
    

class MainCommand(Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    group = SlashCommandGroup("tag", "태그와 번역본을 검색하거나 등록합니다.")

    @group.command(
        name="get", 
        description="태그 정보를 가져옵니다."
    )
    async def get_tag(
        self,
        ctx, 
        prefix: discord.Option(
            str,
            "태그의 종류를 나타냅니다.",
            choices=[
                discord.OptionChoice(
                    name="female(여성)",
                    value="female"
                ),
                discord.OptionChoice(
                    name="male(남성)",
                    value="male"
                ),
                discord.OptionChoice(
                    name="type(공통)",
                    value="type"
                )
            ]
        ), 
        name: discord.Option(
            str, 
            "태그를 입력해주세요.\n(띄어쓰기는 _로 처리)"
        )
    ):
        embed = discord.Embed(title="검색 결과")
        query = f"SELECT * FROM Tags WHERE prefix='{prefix}' AND tag='{name}'"
        query_result = DB_OBJECT.execute_result(query)
        if not query_result:
            embed.description = "태그가 존재하지 않습니다.\n철자를 확인하고 다시 시도해주세요."
            embed.color = 0xff3232
        else:
            default_data = '정보가 등록되지 않았습니다.'
            data = query_result[0]
            embed.add_field(
                name='태그',
                value=f'{data[0]}:{data[1]}',
                inline=False
            )
            embed.add_field(
                name="작품 개수",
                value=f'{data[2]} 개',
                inline=True
            )
            korean_tag = f'{data[0]}:{data[3]}' if data[3] else default_data
            korean_desc = data[4] if data[4] else default_data
            embed.add_field(
                name="한국어 정보",
                value=f'태그 번역 \n**{korean_tag}**\n\n태그 설명 \n{korean_desc}',
                inline=False
            )
            embed.color = 0x32FF32
        embed.add_field(
            name="개발자 먹여살리기",
            value=embed_supporter_text,
            inline=False
        )
        await ctx.respond(embed=embed)
    
    @group.command(
        name="post",
        description="한국어 번역과 설명을 추가합니다."
    )
    async def post_tag(
        self,
        ctx,
        prefix:discord.Option(
            str,
            "태그의 종류를 나타냅니다.",
            choices=[
                discord.OptionChoice(
                    name="female(여성)",
                    value="female"
                ),
                discord.OptionChoice(
                    name="male(남성)",
                    value="male"
                ),
                discord.OptionChoice(
                    name="type(공통)",
                    value="type"
                )
            ]
        ),
        name: discord.Option(
            str, 
            "태그를 입력해주세요.\n(띄어쓰기는 _로 처리)"
        ),
        tag_translate: discord.Option(
            str,
            "태그를 번역해주세요. 설명과는 다르게 핵심만 요약해주세요."
        )=None,
        description: discord.Option(
            str,
            "태그에 대한 설명을 한국어로 입력해주세요.\n(줄바꿈은 \\n로 처리)"
        )=None
    ):
        error_embed = discord.Embed(title="오류", color=0xff3232)

        if not (tag_translate or description):
            error_embed.description = "태그 번역 혹은 설명을 추가해야 합니다."
            await ctx.respond(embed=error_embed)
            return

        sql = f"SELECT * FROM Tags WHERE prefix='{prefix}' AND tag='{name}'"
        tag_query_result = DB_OBJECT.execute_result(sql)
        if not tag_query_result:
            error_embed.description = "태그가 존재하지 않습니다."
            await ctx.respond(embed=error_embed)
            return

        success_embed = discord.Embed(
            title="추가 처리 완료",
            description="관리자에게 추가 요청이 전송되었습니다.\n24시간 이내에 처리됩니다."
        )
        admin_notice_embed = discord.Embed(
            title="추가 요청",
            description="추가 요청이 전송되었습니다."
        )

        success_embed.add_field(
            name="태그 번역",
            value=str(tag_translate)
        )
        admin_notice_embed.add_field(
            name="태그 번역",
            value=str(tag_translate)
        )
        
        success_embed.add_field(
            name="태그 설명",
            value=str(description).replace("￦n", "\n"),
            inline=False
        )
        admin_notice_embed.add_field(
            name="태그 설명",
            value=str(description).replace("￦n", "\n"),
            inline=False
        )

        success_embed.add_field(
            name="개발자 먹여살리기",
            value=embed_supporter_text,
            inline=False
        )

        await ctx.respond(embed=success_embed)
        channel = await self.bot.fetch_channel(int(manage_channel_id))
        await channel.send(
            embed=admin_notice_embed, 
            view=TagConfirmView(
                ctx,
                prefix=prefix,
                origin=name,
                tag=tag_translate, 
                desc=description,
                author=ctx.author.id,
                bot=self.bot
            )
        )
    
    @group.command(
        name="search",
        description="입력과 유사한 태그를 불러옵니다.\n(현재는 영어 검색만 가능합니다.)"
    )
    async def search_tag(
        self,
        ctx,
        prefix:discord.Option(
            str,
            "태그의 종류를 나타냅니다.",
            choices=[
                discord.OptionChoice(
                    name="female(여성)",
                    value="female"
                ),
                discord.OptionChoice(
                    name="male(남성)",
                    value="male"
                ),
                discord.OptionChoice(
                    name="type(공통)",
                    value="type"
                )
            ]
        ),
        tag: discord.Option(
            str,
            "검색할 태그 이름을 적어주세요."
        ),
        search_limit: discord.Option(
            int,
            "검색 한도를 정해주세요. (기본 10)"
        ) = 10
    ):
        query_result = []
        sql = "SELECT * FROM Tags WHERE prefix='{}' AND tag LIKE '{}'"

        for i in range(0, -len(tag)-1, -1):
            newtag = tag[0:i] + '_'*i if i != 0 else tag
            query_result += DB_OBJECT.execute_result(sql.format(prefix, newtag))
            query_result += DB_OBJECT.execute_result(sql.format(prefix, newtag+"%"))
            if len(query_result) >= search_limit:
                query_result = query_result[:search_limit]
                break
        
        if query_result:
            result_text = "\n\n".join([f"{item[0]}:{item[1]} ({item[2]}개 작품)" for item in query_result])
        else:
            result_text = "입력한 내용을 찾을 수 없었어요.\n"

        embed = discord.Embed(title=f'검색 결과 (상위 {str(search_limit)}개)')
        embed.add_field(name="결과", value=result_text)
        embed.add_field(
            name="개발자 먹여살리기",
            value=embed_supporter_text,
            inline=False
        )
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(MainCommand(bot))
