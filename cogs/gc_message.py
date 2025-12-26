import discord
from discord.ext import commands
from utils.handler import load_data # gc_data.json用
from utils.mapping import update_message_map # gc_mapping.json用
from utils.mutelist import load_mute_list # ★ gc_mute.json用に追加
import traceback 

class GlobalChatMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # グローバルチャットの登録データをロード (gc_data.json)
        self.channels = load_data() 

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        グローバルチャットに登録されたチャンネルからのメッセージを他のチャンネルに転送します。
        転送後、元のメッセージIDと転送先メッセージIDの紐付けを保存します。
        """
        
        # 1. フィルタリングと初期チェック
        
        # 自分のメッセージ、DM、Webhookからのメッセージは無視
        if message.author.bot or message.webhook_id or not message.guild:
            return
            
        guild_id = str(message.guild.id)

        # ★ 1.1. ミュートユーザーのメッセージを無視
        mute_list = load_mute_list()
        if message.author.id in mute_list:
            return # ミュートユーザーのメッセージは転送しない
        
        # 1.2. 登録サーバーか、登録チャンネルかチェック
        if guild_id not in self.channels:
            return 
            
        registered_channel_id = self.channels[guild_id]["channel_id"]
        
        if message.channel.id != registered_channel_id:
            return 
            
        # 2. Webhook送信パラメータの準備
        
        display_name = message.author.display_name
        guild_name = message.guild.name
        original_message_id = message.id # 元のメッセージIDを取得
        
        # ★ 2.1. Webhookのユーザー名にメッセージIDを追加
        webhook_username = f"{display_name} ({guild_name}) - {original_message_id}"
        
        avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
        
        content = message.content
        files_to_send = []

        # 2.2. 添付ファイル処理
        if message.attachments:
            try:
                files_to_send = [await attachment.to_file() for attachment in message.attachments]
            except Exception as e:
                print(f"CRITICAL: Failed to process attachments for message {message.id}. Error: {e}")
                return 

        if not content and not files_to_send:
            return
            
        # 3. メッセージの転送とIDの保存
        
        # 転送されている全てのチャンネルをループ
        for target_guild_id, channel_info in self.channels.items():
            
            if target_guild_id == guild_id:
                continue
                
            webhook_url = channel_info["webhook_url"]
            
            try:
                webhook = discord.Webhook.from_url(webhook_url, client=self.bot) 
                
                # wait=True で Webhook送信し、送信メッセージオブジェクトを取得
                sent_message = await webhook.send(
                    content=content,
                    username=webhook_username, # IDを含むユーザー名
                    avatar_url=avatar_url,
                    files=files_to_send,
                    wait=True, # ★ 転送先メッセージIDを取得するために必須
                    allowed_mentions=discord.AllowedMentions.none() 
                )
                
                # ★ 成功: 転送先メッセージIDをマッピングファイルに保存
                update_message_map(
                    original_message_id=original_message_id, 
                    target_guild_id=target_guild_id, 
                    target_message_id=sent_message.id # 取得した転送先メッセージIDを使用
                )
                
            except discord.NotFound:
                print(f"WARNING: Webhook for guild {target_guild_id} not found. Skipping.")
                continue
            except Exception as e:
                print(f"CRITICAL ERROR during webhook send to {target_guild_id}:")
                traceback.print_exc()
                continue
                
        # 添付ファイルオブジェクトを閉じる
        for file in files_to_send:
            file.close()


async def setup(bot):
    await bot.add_cog(GlobalChatMessage(bot))