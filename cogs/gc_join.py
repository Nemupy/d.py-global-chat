import discord
from discord.ext import commands
from utils.handler import load_data, save_data # utils/handler.pyから関数をインポート

class GlobalChatJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # データハンドラから現在のグローバルチャットデータをロード
        # 構造: {サーバーID: {"channel_id": int, "webhook_url": str}}
        self.channels = load_data()

    @commands.command(name='gc_join')
    @commands.guild_only() # DMでの実行を禁止
    @commands.has_permissions(manage_webhooks=True) # Webhook管理権限を持つユーザーのみ実行可能
    async def gc_join(self, ctx: commands.Context):
        """
        現在のチャンネルをグローバルチャットに参加させます。
        (1サーバーにつき1チャンネルのみ)
        """
        
        # 1. 初期チェックと権限確認
        guild_id = str(ctx.guild.id)
        
        # 権限チェックはデコレータで行っているが、念のためボットの権限を確認
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks:
            await ctx.send(
                "🚨 **エラー**: 私はこのチャンネルでWebhookを作成する権限がありません。"
                " `Webhookの管理` 権限を与えてください。"
            )
            return

        # 2. 1サーバー1チャンネルの制限チェック
        if guild_id in self.channels:
            current_channel_id = self.channels[guild_id].get("channel_id")
            current_channel = self.bot.get_channel(current_channel_id)
            
            # 既に登録されているチャンネルがまだ存在するか確認
            if current_channel:
                 await ctx.send(
                    f"❌ **登録失敗**: このサーバーは既にグローバルチャットにチャンネル **#{current_channel.name}** を登録しています。"
                    " 別のチャンネルを登録するには、まず `gc_leave` コマンドで解除してください。"
                )
            else:
                # チャンネルは消えているがデータが残っている場合（データ上は登録済みとする）
                await ctx.send(
                    f"❌ **登録失敗**: データに登録情報が残っていますが、チャンネルが見つかりません。`gc_leave` コマンドでデータ上の登録を解除してください。"
                )
            return
            
        # 3. Webhookの作成
        try:
            # チャンネル名が長すぎる場合は切り詰めるか、別名を使用
            webhook_name = f"GC-Relay-{ctx.guild.name}"[:32] 
            
            # Webhookを作成 (awaitが必要)
            webhook = await ctx.channel.create_webhook(
                name=webhook_name, 
                reason="Global Chat Relay Registration"
            )
            
            webhook_url = webhook.url
            
        except discord.Forbidden:
            # manage_webhooksデコレータをすり抜けた場合や、チャンネル固有の権限不足の場合
            await ctx.send("🚨 **致命的なエラー**: Webhookを作成できませんでした。ボットがチャンネルに必要な権限を持っているか確認してください。")
            return
        except Exception as e:
            print(f"Webhook creation failed: {e}")
            await ctx.send(f"⚠️ **予期せぬエラー**: Webhookの作成中に問題が発生しました。詳細: {e}")
            return

        # 4. データの保存と完了通知
        
        # 新しいデータを辞書に格納
        new_entry = {
            "channel_id": ctx.channel.id,
            "webhook_url": webhook_url
        }
        
        # 内部変数とファイルにデータを保存
        self.channels[guild_id] = new_entry
        save_data(self.channels)

        await ctx.send(
            f"🎉 **グローバルチャット登録完了！**\n"
            f"現在のチャンネル **#{ctx.channel.name}** をグローバルチャットに接続しました。"
        )

# Cogをセットアップする非同期関数（main.pyでロードするために必要）
async def setup(bot):
    await bot.add_cog(GlobalChatJoin(bot))