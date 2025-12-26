import discord
from discord.ext import commands
from utils.mutelist import add_user_to_mute_list, load_mute_list

# コマンドの実行を許可するギルドとロールのID
TARGET_GUILD_ID = 1355794280815394816
TARGET_ROLE_ID = 1437066084946546892

class GlobalChatMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_authorized(self, ctx: commands.Context) -> bool:
        """指定されたギルドとロールを持っているかチェックする。"""
        if ctx.guild.id != TARGET_GUILD_ID:
            return False
            
        role = ctx.guild.get_role(TARGET_ROLE_ID)
        if role and role in ctx.author.roles:
            return True
            
        return False

    @commands.command(name='gc_mute')
    @commands.guild_only()
    async def gc_mute(self, ctx: commands.Context, user: discord.User = None):
        """
        指定したユーザーをグローバルチャットからミュートする。
        実行は特定のギルド・ロール保持者に限定されます。
        """
        
        # 1. 権限チェック
        if not self.is_authorized(ctx):
            await ctx.send("❌ **権限エラー**: このコマンドは、指定されたサーバーで特定のロールを持つユーザーのみ実行できます。")
            return
            
        if user is None:
            await ctx.send("❌ **引数エラー**: ミュートするユーザーをIDまたはメンションで指定してください。例: `!gc_mute @user` または `!gc_mute 1234567890`")
            return
            
        # 2. ミュートリストに追加
        user_id = user.id
        
        if add_user_to_mute_list(user_id):
            await ctx.send(f"✅ **ミュート完了**: ユーザー **{user.display_name} ({user_id})** をグローバルチャットからミュートしました。")
        else:
            await ctx.send(f"⚠️ **既にミュート済み**: ユーザー **{user.display_name} ({user_id})** は既にミュートリストに含まれています。")

    @gc_mute.error
    async def gc_mute_error(self, ctx: commands.Context, error):
        """ミュートコマンド実行時のエラー処理"""
        if isinstance(error, commands.UserNotFound):
            await ctx.send("❌ **ユーザーエラー**: 指定されたIDまたはメンションのユーザーが見つかりませんでした。")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ **引数エラー**: ミュートするユーザーを指定してください。")
        else:
            print(f"An unexpected error occurred in gc_mute: {error}")
            await ctx.send(f"❌ **予期せぬエラー**: コマンド実行中にエラーが発生しました。")


async def setup(bot):
    await bot.add_cog(GlobalChatMute(bot))