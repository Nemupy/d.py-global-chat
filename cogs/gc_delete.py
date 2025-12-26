import discord
from discord.ext import commands
from utils.handler import load_data # gc_data.json用
from utils.mapping import load_message_map, delete_message_mapping
import traceback

class GlobalChatDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # gc_data.jsonをロード（Webhook URLを取得するために必要）
        self.gc_channels = load_data() 

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        グローバルチャットに登録されたチャンネルでメッセージが削除されたとき、
        関連する全ての転送先メッセージを削除します。
        """
        
        # 1. 初期チェック
        # DMやWebhookが削除したメッセージは無視
        if not message.guild or message.webhook_id:
            return
            
        guild_id = str(message.guild.id)
        
        # 削除されたメッセージがグローバルチャットチャンネルからのものか確認
        if guild_id not in self.gc_channels:
            return # 登録されていないサーバーからの削除は無視
            
        registered_channel_id = self.gc_channels[guild_id]["channel_id"]
        
        if message.channel.id != registered_channel_id:
            return # 登録チャンネル以外での削除は無視
            
        # 2. メッセージマッピングの取得
        original_message_id = message.id
        
        # gc_mapping.jsonからマッピングデータをロード
        all_mappings = load_message_map()
        original_id_str = str(original_message_id)

        if original_id_str not in all_mappings:
            # 転送されたメッセージでなければ無視
            return

        transfer_list = all_mappings[original_id_str]
        
        # 3. 全転送先メッセージの削除
        
        for item in transfer_list:
            target_guild_id = item['guild_id']
            target_message_id = item['message_id']
            
            # 転送先のWebhook URLを取得
            if target_guild_id not in self.gc_channels:
                print(f"WARNING: Target guild {target_guild_id} not found in gc_data. Skipping delete.")
                continue
                
            webhook_url = self.gc_channels[target_guild_id]['webhook_url']
            
            try:
                # Webhookオブジェクトを構築
                webhook = discord.Webhook.from_url(webhook_url, client=self.bot)
                
                # Webhook APIを使ってメッセージを削除
                await webhook.delete_message(target_message_id) 
                
            except discord.NotFound:
                # 既に削除されている場合は成功とみなす
                print(f"INFO: Target message {target_message_id} already deleted.")
                pass
            except Exception as e:
                # その他のエラー発生時
                print(f"CRITICAL ERROR during message deletion to guild {target_guild_id}:")
                traceback.print_exc()
                continue
                
        # 4. マッピングデータからのエントリ削除
        # 転送先すべての削除を試みた後、紐付けデータを削除
        delete_message_mapping(original_message_id)
        print(f"INFO: Successfully processed and cleaned up mapping for original message {original_message_id}.")


async def setup(bot):
    await bot.add_cog(GlobalChatDelete(bot))