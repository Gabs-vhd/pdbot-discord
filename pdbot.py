# -*- coding: utf-8 -*-

# ========================================================================================
#                                IMPORTS E BIBLIOTECAS
# ========================================================================================
import discord
from discord.ext import commands
import re
import random
import json
import os
import asyncio

# ========================================================================================
#                               CONFIGURAÇÃO INICIAL DO BOT
# ========================================================================================

# --- Constantes de Arquivos ---
USER_DATA_FILE = "database.json"
INITIATIVE_FILE = "initiative.json"

# --- Configuração do Bot e Intents ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("pd."), intents=intents)
# Remove o comando de ajuda padrão para podermos criar o nosso
bot.remove_command('help')

# ========================================================================================
#                               FUNÇÕES AUXILIARES
# ========================================================================================

def load_data(file_path):
    """Carrega dados de um arquivo JSON. Retorna um dicionário vazio se não existir."""
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data, file_path):
    """Salva dados em um arquivo JSON com formatação."""
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def process_roll(roll_input: str):
    pattern = r"(\d+#)?(\d*)d(\d+)([+-]\d+)?"
    match = re.fullmatch(pattern, roll_input.replace(" ", ""))
    if not match: return "error", "❌ Formato inválido.", None
    
    count_str, num_dice_str, dice_sides_str, modifier_str = match.groups()
    count = int(count_str[:-1]) if count_str else 1
    num_dice = int(num_dice_str) if num_dice_str else 1
    dice_sides = int(dice_sides_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    if count > 1: return "error", "❌ O comando de iniciativa só suporta uma rolagem por vez (ex: 1d20+3).", None

    rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
    soma_dados = sum(rolls)
    total_final = soma_dados + modifier
    
    mod_string = f"{modifier:+}" if modifier != 0 else ""
    formula_str = f"{num_dice}d{dice_sides}{mod_string}"
    rolls_str = " ".join(f"`{r}`" for r in rolls)
    texto_resposta = f"**Comando:** `{formula_str}`\n🎲 **Dados:** {rolls_str} (Soma: `{soma_dados}`)\n"
    if modifier != 0: texto_resposta += f"**⚙️ Modificador:** `{modifier:+}`\n"
    texto_resposta += f"**📊 Total:** **{total_final}**"
    
    return "success", texto_resposta, total_final

# ========================================================================================
#                                 CARREGAMENTO DE DADOS
# ========================================================================================

user_data = load_data(USER_DATA_FILE)
initiative_data = load_data(INITIATIVE_FILE)

# ========================================================================================
#                                   EVENTOS DO BOT
# ========================================================================================

@bot.event
async def on_ready():
    """Evento executado quando o bot está online e pronto."""
    print("----------------------------------------")
    print(f"🤖 Bot conectado como {bot.user}!")
    print(f"📊 {len(user_data)} perfis de usuários carregados.")
    print(f"⚔️ {len(initiative_data)} listas de iniciativa carregadas.")
    print("----------------------------------------")

# ========================================================================================
#                              COMANDOS: GESTÃO E AJUDA
# ========================================================================================

@bot.command(name="help")
async def help_command(ctx):
    """Mostra esta mensagem de ajuda."""
    embed = discord.Embed(
        title="🤖 Comandos do pd.BOT",
        description="Aqui está a lista de todos os comandos disponíveis.",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="👤 Gestão de Personagem",
        value="`pd.register` - Cria sua ficha no bot.\n"
              "`pd.register remover` - Apaga sua ficha.\n"
              "`pd.attribute` - Mostra seus atributos.\n"
              "`pd.attribute_push <attr=valor>` - Adiciona/atualiza atributos.\n"
              "`pd.attribute_remove <attr>` - Remove atributos.\n"
              "`pd.gear` - Mostra seu inventário.\n"
              "`pd.gear +/-<qtd> <item>` - Adiciona/remove itens.\n"
              "`pd.hp` - Mostra sua vida atual.\n"
              "`pd.hp +/-<valor>` - Cura ou causa dano.\n"
              "`pd.hp set <valor>` - Define sua vida máxima.",
        inline=False
    )
    embed.add_field(
        name="💰 Finanças",
        value="`pd.money [@usuario]` - Mostra seu saldo ou de outra pessoa.\n"
              "`pd.add_money <valor>` - Adiciona dinheiro à sua conta.\n"
              "`pd.pop_money <valor>` - Remove dinheiro da sua conta.",
        inline=False
    )
    embed.add_field(
        name="⚔️ Ações e Combate",
        value="`pd.roll <dado>` - Rola um ou mais dados (ex: `pd.roll 2#d20+3`).\n"
              "`pd.sroll <dado>` - Faz uma rolagem secreta para você.\n"
              "`pd.init <rolagem>` - Rola e entra na lista de iniciativa.\n"
              "`pd.init_list` - Mostra a ordem de iniciativa.\n"
              "`pd.init_clear` - Limpa a lista de iniciativa.",
        inline=False
    )
    embed.set_footer(text=f"Use o prefixo 'pd.' antes de cada comando.")
    await ctx.send(embed=embed)

@bot.command(name="register")
async def register(ctx, action: str = None):
    """Registra você ou remove seu perfil do bot."""
    user_id = str(ctx.author.id)
    if action and action.lower() == 'remover':
        if user_id not in user_data:
            return await ctx.send("🤔 Você não está registrado, então não há nada para remover.")
        
        await ctx.send(f"⚠️ **Atenção, {ctx.author.mention}!** Esta ação é **irreversível**.\nDigite `sim` para confirmar.")
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        try:
            confirmation_msg = await bot.wait_for('message', timeout=30.0, check=check)
            if confirmation_msg.content.lower() == 'sim':
                del user_data[user_id]
                save_data(user_data, USER_DATA_FILE) 
                await ctx.send("✅ Seus dados foram removidos com sucesso.")
            else:
                await ctx.send("❌ Remoção cancelada.")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado. A remoção foi cancelada.")
        return

    if user_id in user_data:
        await ctx.send("✅ Você já está registrado!")
    else:
        user_data[user_id] = {"name": ctx.author.name, "money": 0, "inventory": {}, "hp_atual": 10, "hp_max": 10, "attributes": {}}
        save_data(user_data, USER_DATA_FILE) # Passando o caminho do arquivo
        await ctx.send(f"🎉 Bem-vindo, {ctx.author.mention}! Você foi registrado. Use `pd.hp set <valor>`.")

# ========================================================================================
#                         COMANDOS: ATRIBUTOS E PERSONAGEM
# ========================================================================================

@bot.command(name="attribute")
async def attribute_list(ctx, member: discord.Member = None):
    """Mostra seus atributos ou os de outro membro."""
    target_user = member or ctx.author
    user_id = str(target_user.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ {target_user.display_name} não está registrado(a).")

    attributes = user_data[user_id].get("attributes", {})
    embed = discord.Embed(title=f"📜 Atributos de {target_user.display_name}", color=discord.Color.blue())
    if not attributes:
        embed.description = "Nenhum atributo definido."
    else:
        embed.description = "\n".join([f"**{name.upper()}:** {value}" for name, value in attributes.items()])
    await ctx.send(embed=embed)

@bot.command(name="attribute_push")
async def attribute_push(ctx, *, args: str):
    """Adiciona ou atualiza atributos na sua ficha. Ex: for=10, des=14"""
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        return await ctx.send("⚠️ Você não está registrado. Use `pd.register` primeiro.")

    attributes_to_add = re.findall(r'([a-zA-Z_]+)\s*=\s*(-?\d+)', args)
    if not attributes_to_add:
        return await ctx.send("❌ Formato inválido. Use `pd.attribute_push nome=valor, outro=valor`.")

    if "attributes" not in user_data[user_id]:
        user_data[user_id]["attributes"] = {}
    
    added_feedback = [f"`{name.upper()}`=`{val}`" for name, val in attributes_to_add]
    for attr_name, attr_value in attributes_to_add:
        user_data[user_id]["attributes"][attr_name.lower()] = int(attr_value)
    
    save_data(user_data, USER_DATA_FILE)
    await ctx.send(f"✅ Atributos atualizados: {', '.join(added_feedback)}")

@bot.command(name="attribute_remove")
async def attribute_remove(ctx, *, args: str):
    """Remove atributos da sua ficha. Ex: for, des"""
    user_id = str(ctx.author.id)
    if user_id not in user_data or "attributes" not in user_data.get(user_id, {}):
        return await ctx.send("⚠️ Você não tem atributos para remover.")
    
    attributes_to_remove = [attr.strip().lower() for attr in args.split(',')]
    removed_feedback = []
    for attr_name in attributes_to_remove:
        if attr_name in user_data[user_id]["attributes"]:
            del user_data[user_id]["attributes"][attr_name]
            removed_feedback.append(f"`{attr_name.upper()}`")
    
    if not removed_feedback:
        return await ctx.send("🤔 Nenhum dos atributos mencionados foi encontrado na sua ficha.")
        
    save_data(user_data, USER_DATA_FILE)
    await ctx.send(f"🗑️ Atributos removidos: {', '.join(removed_feedback)}")
    
@bot.command(name="hp")
async def hp_command(ctx, *, args: str = None):
    """Gerencia seus Pontos de Vida. Use pd.hp, pd.hp set <valor>, pd.hp +/-<valor>."""
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ Você não está registrado. Use `pd.register` primeiro.")

    profile = user_data[user_id]
    
    if args is None:
        hp_atual = profile.get("hp_atual", 0)
        hp_max = profile.get("hp_max", 1)
        health_percentage = hp_atual / hp_max
        filled_blocks = int(health_percentage * 10)
        empty_blocks = 10 - filled_blocks
        health_bar = f"[`{'█' * filled_blocks}{'░' * empty_blocks}`]"
        embed = discord.Embed(
            title=f"❤️ Pontos de Vida de {ctx.author.display_name}",
            description=f"**{hp_atual} / {hp_max}**\n{health_bar}",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    match_set = re.match(r"(set|max)\s+(\d+)", args, re.IGNORECASE)
    if match_set:
        valor = int(match_set.group(2))
        if valor <= 0:
            return await ctx.send("❌ O HP máximo deve ser maior que zero.")
        profile["hp_max"] = valor
        profile["hp_atual"] = valor
        save_data(user_data, USER_DATA_FILE) # CORRIGIDO
        return await ctx.send(f"✅ HP máximo de {ctx.author.mention} definido para **{valor}**! Você foi curado.")

    try:
        valor = int(args.replace(" ", ""))
        hp_atual = profile.get("hp_atual", 0)
        hp_max = profile.get("hp_max", hp_atual)
        novo_hp = max(0, min(hp_max, hp_atual + valor))
        profile["hp_atual"] = novo_hp
        save_data(user_data, USER_DATA_FILE) # CORRIGIDO
        acao = "curou" if novo_hp > hp_atual else "recebeu"
        diferenca = abs(novo_hp - hp_atual)
        await ctx.send(f"❤️ {ctx.author.mention} {acao} **{diferenca}** de dano/cura.\nSua vida agora é **{novo_hp} / {hp_max}**.")
    except ValueError:
        await ctx.send("❌ Comando de HP inválido. Use `pd.hp`, `pd.hp set <valor>`, ou `pd.hp +/-<valor>`.")
        
@bot.command(name="gear")
async def gear(ctx, *, args: str = None):
    """Gerencia seu inventário. Use sem argumentos para ver, ou +/-<qtd> <item> para modificar."""
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ Você não está registrado. Use `pd.register` primeiro.")

    # Se nenhum argumento for dado, mostra o inventário
    if args is None:
        inventory = user_data[user_id].get("inventory", {})
        embed = discord.Embed(title=f"🎒 Inventário de {ctx.author.display_name}", color=discord.Color.dark_gold())
        if not inventory:
            embed.description = "Seu inventário está vazio."
        else:
            embed.description = "\n".join([f"**{item}**: `x{qtd}`" for item, qtd in inventory.items()])
        return await ctx.send(embed=embed)

    # Regex para extrair o sinal (+/-), a quantidade e o nome do item
    match = re.match(r"\s*([+-])?\s*(\d+)?\s*(.+)", args.strip())
    if not match:
        return await ctx.send("❌ Formato inválido. Use `pd.gear`, `pd.gear +1 Poção` ou `pd.gear -1 Flecha`.")

    sign, quantity_str, item_name = match.groups()
    item_name = item_name.strip().capitalize()
    if not item_name:
        return await ctx.send("❌ Você precisa especificar o nome do item.")

    quantity = int(quantity_str) if quantity_str else 1
    inventory = user_data[user_id].get("inventory", {})
    current_quantity = inventory.get(item_name, 0)

    if sign == '-':
        if current_quantity < quantity:
            return await ctx.send(f"🤔 Você não tem **{quantity} {item_name}** para remover. Você possui apenas `{current_quantity}`.")
        inventory[item_name] = current_quantity - quantity
        if inventory[item_name] == 0:
            del inventory[item_name]
        action_text = f"🗑️ Removido `{quantity} {item_name}`."
    else: # Adicionar é o padrão se não houver sinal
        inventory[item_name] = current_quantity + quantity
        action_text = f"✅ Adicionado `{quantity} {item_name}`."

    user_data[user_id]["inventory"] = inventory
    save_data(user_data, USER_DATA_FILE)

    new_quantity = inventory.get(item_name, 0)
    await ctx.send(f"{action_text} Novo total: `{new_quantity}`.")

# ========================================================================================
#                              COMANDOS: FINANÇAS
# ========================================================================================

@bot.command(name="money")
async def money(ctx, member: discord.Member = None):
    """Mostra o seu saldo ou o de outro membro."""
    target_user = member or ctx.author
    user_id = str(target_user.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ {target_user.display_name} não está registrado(a).")

    balance = user_data[user_id].get("money", 0)
    await ctx.send(f"💰 O saldo de **{target_user.display_name}** é de **{balance}** moedas.")

@bot.command(name="add_money")
async def add_money(ctx, amount: int):
    """Adiciona dinheiro à sua própria conta."""
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ Você não está registrado. Use `pd.register` primeiro.")
    if amount <= 0:
        return await ctx.send("❌ O valor para adicionar deve ser um número positivo.")

    user_data[user_id]["money"] = user_data[user_id].get("money", 0) + amount
    save_data(user_data, USER_DATA_FILE)
    new_balance = user_data[user_id]["money"]
    await ctx.send(f"💸 Adicionado **{amount}** moedas. Seu novo saldo é: **{new_balance}**.")

@bot.command(name="pop_money")
async def pop_money(ctx, amount: int):
    """Remove dinheiro da sua própria conta."""
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        return await ctx.send(f"⚠️ Você não está registrado. Use `pd.register` primeiro.")
    if amount <= 0:
        return await ctx.send("❌ O valor para remover deve ser um número positivo.")

    current_balance = user_data[user_id].get("money", 0)
    if current_balance < amount:
        return await ctx.send(f"🤔 Você não pode remover **{amount}** moedas. Seu saldo é de apenas **{current_balance}**.")

    user_data[user_id]["money"] = current_balance - amount
    save_data(user_data, USER_DATA_FILE)
    new_balance = user_data[user_id]["money"]
    await ctx.send(f"💸 Removido **{amount}** moedas. Seu novo saldo é: **{new_balance}**.")

# ========================================================================================
#                            COMANDOS: AÇÃO E COMBATE
# ========================================================================================

@bot.command(name="init")
async def initiative_roll(ctx, *, roll_input: str):
    """Rola a sua iniciativa e te adiciona à lista de combate."""
    user = ctx.author
    channel_id = str(ctx.channel.id)

    # CORREÇÃO: Chama a função de iniciativa específica
    status, resultado, total_final = process_initiative_roll(roll_input)

    if status == "error":
        await ctx.send(f"{user.mention} {resultado}")
        return

    if channel_id not in initiative_data:
        initiative_data[channel_id] = {}

    initiative_data[channel_id][str(user.id)] = {
        "name": user.display_name,
        "score": total_final
    }
    
    save_data(initiative_data, INITIATIVE_FILE)
    
    await ctx.send(f"✅ **{user.display_name}** entrou na iniciativa com o valor **{total_final}**.\n> {resultado.replace(chr(10), chr(10)+'> ')}")

@bot.command(name="init_list")
async def initiative_list(ctx):
    """Mostra a ordem de iniciativa para o canal atual."""
    channel_id = str(ctx.channel.id)

    if channel_id not in initiative_data or not initiative_data[channel_id]:
        await ctx.send("⚔️ A lista de iniciativa está vazia. Use `pd.init <rolagem>` para começar!")
        return

    sorted_initiatives = sorted(
        initiative_data[channel_id].values(),
        key=lambda x: x["score"],
        reverse=True
    )

    embed = discord.Embed(
        title="⚔️ Ordem de Iniciativa ⚔️",
        color=discord.Color.dark_red()
    )

    description = ""
    for i, participant in enumerate(sorted_initiatives):
        description += f"**{i+1}.** {participant['name']} - `{participant['score']}`\n"

    embed.description = description
    await ctx.send(embed=embed)

@bot.command(name="init_clear")
async def initiative_clear(ctx):
    """Limpa a lista de iniciativa do canal atual."""
    channel_id = str(ctx.channel.id)

    if channel_id in initiative_data:
        del initiative_data[channel_id]
        save_data(initiative_data, INITIATIVE_FILE)
        await ctx.send("✅ A lista de iniciativa foi limpa com sucesso!")
    else:
        await ctx.send("🤔 Não há nenhuma lista de iniciativa para limpar neste canal.")

# ========================================================================================
#                            COMANDOS: ROLAGEM DE DADOS
# ========================================================================================
        
def process_initiative_roll(roll_input: str):
    """
    Processa uma rolagem de dados ESPECÍFICA para iniciativa.
    Retorna: status (str), mensagem (str), valor_total (int)
    """
    pattern = r"(\d+#)?(\d*)d(\d+)([+-]\d+)?"
    match = re.fullmatch(pattern, roll_input.replace(" ", ""))
    if not match: return "error", "❌ Formato inválido.", None
    
    count_str, num_dice_str, dice_sides_str, modifier_str = match.groups()
    count = int(count_str[:-1]) if count_str else 1
    num_dice = int(num_dice_str) if num_dice_str else 1
    dice_sides = int(dice_sides_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    # Validação específica para iniciativa
    if count > 1: return "error", "❌ O comando de iniciativa só suporta uma rolagem por vez (ex: 1d20+3).", None

    rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
    soma_dados = sum(rolls)
    total_final = soma_dados + modifier
    
    mod_string = f"{modifier:+}" if modifier != 0 else ""
    formula_str = f"{num_dice}d{dice_sides}{mod_string}"
    rolls_str = " ".join(f"`{r}`" for r in rolls)
    texto_resposta = f"**Comando:** `{formula_str}`\n🎲 **Dados:** {rolls_str} (Soma: `{soma_dados}`)\n"
    if modifier != 0: texto_resposta += f"**⚙️ Modificador:** `{modifier:+}`\n"
    texto_resposta += f"**📊 Total:** **{total_final}**"
    
    return "success", texto_resposta, total_final

def process_general_roll(roll_input: str):
    """
    Processa rolagens de dados GERAIS (pode ter múltiplas rolagens).
    Retorna: status (str), mensagem_completa (str)
    """
    pattern = r"(\d+#)?(\d*)d(\d+)([+-]\d+)?"
    match = re.fullmatch(pattern, roll_input.replace(" ", ""))
    if not match: return "error", "❌ Formato inválido."
    
    count_str, num_dice_str, dice_sides_str, modifier_str = match.groups()
    count = int(count_str[:-1]) if count_str else 1
    num_dice = int(num_dice_str) if num_dice_str else 1
    dice_sides = int(dice_sides_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    if count > 20 or num_dice > 100 or dice_sides > 1000: return "error", "❌ Limites excedidos (Max: 20#100d1000)."
    
    resultados = []
    for _ in range(count):
        rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
        soma_dados = sum(rolls)
        total_final = soma_dados + modifier
        mod_string = f"{modifier:+}" if modifier != 0 else ""
        formula_str = f"{num_dice}d{dice_sides}{mod_string}"
        rolls_str = " ".join(f"`{r}`" for r in rolls)
        texto_resposta = f"**Comando:** `{formula_str}`\n🎲 **Dados:** {rolls_str} (Soma: `{soma_dados}`)\n"
        if modifier != 0: texto_resposta += f"**⚙️ Modificador:** `{modifier:+}`\n"
        texto_resposta += f"**📊 Total:** **{total_final}**"
        resultados.append(texto_resposta)
        
    return "success", "\n\n".join(resultados)

# --- COMANDOS ---
@bot.command(name="roll")
async def public_roll(ctx, *, entrada: str):
    """Rola um ou mais dados publicamente."""
   
    status, resultado = process_general_roll(entrada)
    if status == "error":
        await ctx.send(f"{ctx.author.mention} {resultado}")
    else:
        await ctx.send(f"**{ctx.author.display_name} rolou:**\n{resultado}")

@bot.command(name="sroll")
async def secret_roll(ctx, *, entrada: str):
    """Faz uma rolagem 100% secreta, enviando o resultado APENAS na DM."""
    
    status, resultado = process_general_roll(entrada) 
    
    try:
        
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass # Ignora se o bot não tiver permissão para apagar mensagens.
        
    if status == "error":
        try:
            # Se der erro, envia o aviso de erro na DM.
            await ctx.author.send(f"⚠️ Erro na sua rolagem secreta: {resultado}")
        except discord.Forbidden:
            # Se não puder enviar a DM, não faz nada para manter o sigilo.
            pass
    else:
        try:
            await ctx.author.send(f"**Sua rolagem secreta:**\n{resultado}")
            
            
        except discord.Forbidden:
            # Se não for possível enviar a DM com o resultado, o bot não fará nada.
            # Isso evita expor no chat público que uma rolagem secreta falhou ao ser enviada.
            print(f"ERRO: Não foi possível enviar DM para o usuário {ctx.author.name}.")
        
# ========================================================================================
#                                EXECUÇÃO DO BOT
# ========================================================================================

def run_bot():
    # Carrega o token de um arquivo de configuração externo
    if not os.path.exists("config.json"):
        print("ERRO: Arquivo 'config.json' não encontrado! Crie o arquivo com seu token.")
        return
        
    with open("config.json") as f:
        config = json.load(f)
        token = config.get("token")

    if not token:
        print("ERRO: Token não encontrado dentro de 'config.json'!")
        return

    bot.run(token)

if __name__ == "__main__":
    run_bot()