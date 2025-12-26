import discord
from discord.ext import commands
from utils.handler import load_data # gc_data.json用
from utils.mapping import load_message_map
import traceback

class GlobalChatEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Webhook URLを取得するために必要
        self.gc_channels = load_data() 

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        グローバルチャットに登録されたチャンネルでメッセージが編集されたとき、
        関連する全ての転送先メッセージを編集します。
        """
        
        # 1. フィルタリングと初期チェック
        # Botによる編集、内容が変わっていない、DM/システムメッセージの場合は無視
        if after.author.bot or before.content == after.content or not after.guild:
            return
            
        guild_id = str(after.guild.id)
        
        # 登録チャンネルのチェック
        if guild_id not in self.gc_channels:
            return 
            
        registered_channel_id = self.gc_channels[guild_id]["channel_id"]
        
        if after.channel.id != registered_channel_id:
            return 

        # 2. マッピングの取得
        original_message_id = after.id
        all_mappings = load_message_map()
        original_id_str = str(original_message_id)

        if original_id_str not in all_mappings:
            return # 転送されていないメッセージは無視

        transfer_list = all_mappings[original_id_str]
        
        # 3. 編集内容の準備
        
        # ★ 修正: 編集マークを付けずに、編集後のメッセージ内容をそのまま使用
        new_content = after.content
        
        # 4. 全転送先メッセージの編集実行
        
        for item in transfer_list:
            target_guild_id = item['guild_id']
            target_message_id = item['message_id']
            
            if target_guild_id not in self.gc_channels:
                continue
                
            webhook_url = self.gc_channels[target_guild_id]['webhook_url']
            
            try:
                webhook = discord.Webhook.from_url(webhook_url, client=self.bot)
                
                # Webhook APIを使ってメッセージを編集
                # username, avatar_urlは編集できないため渡しません。
                await webhook.edit_message(
                    target_message_id,
                    content=new_content,       # 編集後の新しいメッセージ内容
                    embeds=[], 
                    attachments=[],
                )
                
            except discord.NotFound:
                print(f"INFO: Target message {target_message_id} not found for edit.")
                pass
            except Exception as e:
                print(f"CRITICAL ERROR during message edit to guild {target_guild_id}:")
                traceback.print_exc()
                continue
                
async def setup(bot):
    await bot.add_cog(GlobalChatEdit(bot))