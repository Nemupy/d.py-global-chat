import discord
from discord.ext import commands
from utils.handler import load_data, save_data # utils/handler.pyから関数をインポート

class GlobalChatLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # データハンドラから現在のグローバルチャットデータをロード
        # 構造: {サーバーID: {"channel_id": int, "webhook_url": str}}
        self.channels = load_data()

    @commands.command(name='gc_leave')
    @commands.guild_only() # DMでの実行を禁止
    @commands.has_permissions(manage_webhooks=True) # Webhook管理権限を持つユーザーのみ実行可能
    async def gc_leave(self, ctx: commands.Context):
        """
        現在のサーバーのグローバルチャット登録を解除します。
        """
        
        guild_id = str(ctx.guild.id)
        
        # 1. 登録情報の確認
        if guild_id not in self.channels:
            await ctx.send(
                "❌ **登録されていません**: このサーバーは現在グローバルチャットに参加していません。"
                " 参加するには `gc_join` コマンドを使用してください。"
            )
            return

        # 登録情報を取得
        channel_info = self.channels[guild_id]
        registered_channel_id = channel_info["channel_id"]
        webhook_url = channel_info["webhook_url"]
        
        # 2. Webhookの削除
        try:
            # Webhook URLからWebhookオブジェクトを再構築
            # Webhookを削除するにはHTTPクライアントが必要です
            webhook = discord.Webhook.from_url(webhook_url, client=self.bot.http)
            
            # Webhookを削除
            await webhook.delete(reason="Global Chat Leave Command")
            
        except discord.NotFound:
            # Webhookが既に存在しない場合（手動で削除されたなど）は警告を出すが、処理は続行
            await ctx.send(
                "⚠️ **警告**: 登録されていたWebhookは既に見つかりませんでしたが、データから登録を削除します。"
            )
        except discord.Forbidden:
            # ボットにWebhook削除権限がない場合
            await ctx.send(
                "🚨 **エラー**: Webhookを削除する権限がありません。データからの削除のみを行います。"
            )
        except Exception as e:
            # その他のエラー（URLが無効など）
            print(f"Webhook deletion failed: {e}")
            await ctx.send(f"⚠️ **予期せぬエラー**: Webhookの削除中に問題が発生しました。データからの削除のみを行います。")

        # 3. データの削除と完了通知
        
        # 内部変数からデータを削除
        del self.channels[guild_id]
        
        # ファイルにデータを保存（永続化）
        save_data(self.channels)
        
        # 登録されていたチャンネル名を取得（存在すれば）
        registered_channel = self.bot.get_channel(registered_channel_id)
        channel_name = f"#{registered_channel.name}" if registered_channel else "不明なチャンネル"

        await ctx.send(
            f"👋 **グローバルチャット登録解除完了！**\n"
            f"サーバーのグローバルチャット登録 (**{channel_name}**) を解除しました。"
        )

# Cogをセットアップする非同期関数（main.pyでロードするために必要）
async def setup(bot):
    await bot.add_cog(GlobalChatLeave(bot))