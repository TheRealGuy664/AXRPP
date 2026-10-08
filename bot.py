import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ============================================================
# KONFIGURATION
# ============================================================

TOKEN = "MTU1NzY3NzEyNzc0MTIxMDY2NQ.GXwEza.hJs02njO1unWChZqtYPTxBbt9kIcCyMg9v5Q8Y"
GUILD_ID = 1557518659373502575


# ============================================================
# BOT
# ============================================================

class MyBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()

        # Nødvendigt for at læse svar i DM
        intents.message_content = True

        # Nødvendigt hvis botten skal arbejde med medlemmer/roller
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        guild = discord.Object(id=GUILD_ID)

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print(f"Synkroniserede kommandoer til guild {GUILD_ID}")


bot = MyBot()


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("----------------------------------------")
    print(f"Logget ind som {bot.user} (ID: {bot.user.id})")
    print("Botten er klar!")
    print("----------------------------------------")


# ============================================================
# REVIEW VIEW
# ============================================================

class ReviewView(discord.ui.View):

    def __init__(
        self,
        applicant_id: int,
        app_title: str,
        accepted_role_id: int | None
    ):

        super().__init__(timeout=None)

        self.applicant_id = applicant_id
        self.app_title = app_title
        self.accepted_role_id = accepted_role_id

    async def check_admin(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Kun administratorer kan behandle ansøgninger!",
                ephemeral=True
            )

            return False

        return True

    # ========================================================
    # ACCEPTER
    # ========================================================

    @discord.ui.button(
        label="Accepter",
        style=discord.ButtonStyle.green,
        custom_id="application_accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not await self.check_admin(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        applicant = guild.get_member(self.applicant_id)

        # ----------------------------------------------------
        # GIV ROLLE HVIS EN ER VALGT
        # ----------------------------------------------------

        role_given = False

        if applicant and self.accepted_role_id:

            role = guild.get_role(
                self.accepted_role_id
            )

            if role:

                try:

                    await applicant.add_roles(
                        role,
                        reason=(
                            f"Ansøgning accepteret af "
                            f"{interaction.user}"
                        )
                    )

                    role_given = True

                except discord.Forbidden:

                    await interaction.response.send_message(
                        "⚠️ Ansøgningen blev godkendt, "
                        "men botten kunne ikke give rollen. "
                        "Kontroller at botten har Manage Roles "
                        "og at botten står over rollen.",
                        ephemeral=True
                    )

                    return

        # ----------------------------------------------------
        # SEND DM
        # ----------------------------------------------------

        if applicant:

            try:

                if role_given:

                    message = (
                        f"🎉 **Tillykke!**\n\n"
                        f"Din ansøgning til "
                        f"**{self.app_title}** "
                        f"er blevet **ACCEPTERET**!\n\n"
                        f"Du har fået rollen "
                        f"**{role.name}**."
                    )

                else:

                    message = (
                        f"🎉 **Tillykke!**\n\n"
                        f"Din ansøgning til "
                        f"**{self.app_title}** "
                        f"er blevet **ACCEPTERET**!"
                    )

                await applicant.send(message)

            except discord.Forbidden:
                pass

        # ----------------------------------------------------
        # OPDATER EMBED
        # ----------------------------------------------------

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.green()

        embed.title = (
            f"✅ Ansøgning accepteret af "
            f"{interaction.user.display_name}"
        )

        if role_given:

            embed.set_footer(
                text=f"Godkendt • Rolle givet: {role.name}"
            )

        else:

            embed.set_footer(
                text="Godkendt • Ingen rolle valgt"
            )

        # Deaktiver knapper
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    # ========================================================
    # AFVIS
    # ========================================================

    @discord.ui.button(
        label="Afvis",
        style=discord.ButtonStyle.red,
        custom_id="application_deny"
    )
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not await self.check_admin(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        applicant = guild.get_member(
            self.applicant_id
        )

        # ----------------------------------------------------
        # SEND DM
        # ----------------------------------------------------

        if applicant:

            try:

                await applicant.send(
                    f"❌ **Desværre.**\n\n"
                    f"Din ansøgning til "
                    f"**{self.app_title}** "
                    f"er blevet **AFVIST**."
                )

            except discord.Forbidden:
                pass

        # ----------------------------------------------------
        # OPDATER EMBED
        # ----------------------------------------------------

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        embed.title = (
            f"❌ Ansøgning afvist af "
            f"{interaction.user.display_name}"
        )

        embed.set_footer(
            text="Afvist"
        )

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


# ============================================================
# ANSØGNING START
# ============================================================

class ApplicationStartView(discord.ui.View):

    def __init__(
        self,
        app_title: str,
        questions: list[str],
        accepted_role_id: int | None
    ):

        super().__init__(timeout=None)

        self.app_title = app_title
        self.questions = questions
        self.accepted_role_id = accepted_role_id

    # ========================================================
    # START ANSØGNING
    # ========================================================

    @discord.ui.button(
        label="Ansøg Her",
        style=discord.ButtonStyle.green,
        custom_id="start_application"
    )
    async def start_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            await interaction.user.send(
                f"👋 **Hej {interaction.user.display_name}!**\n\n"
                f"Du har startet ansøgningen:\n"
                f"**{self.app_title}**\n\n"
                f"Du vil få "
                f"**{len(self.questions)} spørgsmål** "
                f"ét ad gangen.\n\n"
                f"⏰ Du har 10 minutter til hvert svar."
            )

            await interaction.followup.send(
                "📩 Jeg har sendt dig en DM med din ansøgning!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ Jeg kunne ikke sende dig en DM.\n\n"
                "Åbn dine Discord privatlivsindstillinger "
                "og tillad beskeder fra servermedlemmer.",
                ephemeral=True
            )

            return

        # Start interview
        asyncio.create_task(
            self.run_interview(
                interaction.user,
                interaction.guild
            )
        )

    # ========================================================
    # INTERVIEW
    # ========================================================

    async def run_interview(
        self,
        user: discord.Member,
        guild: discord.Guild
    ):

        answers = []

        def check(message: discord.Message):

            return (
                message.author.id == user.id
                and isinstance(
                    message.channel,
                    discord.DMChannel
                )
            )

        # ----------------------------------------------------
        # SPØRGSMÅL
        # ----------------------------------------------------

        for number, question in enumerate(
            self.questions,
            start=1
        ):

            try:

                await user.send(
                    f"**Spørgsmål "
                    f"{number}/{len(self.questions)}**\n\n"
                    f"{question}"
                )

                message = await bot.wait_for(
                    "message",
                    check=check,
                    timeout=600
                )

                answers.append(
                    message.content
                )

            except asyncio.TimeoutError:

                try:

                    await user.send(
                        "⏰ **Tid udløbet.**\n\n"
                        "Du brugte mere end 10 minutter "
                        "på at svare.\n\n"
                        "Ansøgningen er derfor annulleret."
                    )

                except discord.Forbidden:
                    pass

                return

        # ----------------------------------------------------
        # FÆRDIG
        # ----------------------------------------------------

        try:

            await user.send(
                "✅ **Tak!**\n\n"
                "Din ansøgning er færdig og sendt "
                "til ledelsen."
            )

        except discord.Forbidden:
            pass

        # ----------------------------------------------------
        # FIND ANSØGNINGSKANAL
        # ----------------------------------------------------

        channel = guild.get_channel(
            APPLICATION_CHANNELS.get(
                self.app_title,
                0
            )
        )

        if channel is None:
            return

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title=f"📥 Ny Ansøgning: {self.app_title}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=f"{user.name} ({user.id})",
            icon_url=user.display_avatar.url
        )

        for question, answer in zip(
            self.questions,
            answers
        ):

            # Discord max 1024 tegn i et field
            if len(answer) > 1024:
                answer = answer[:1021] + "..."

            embed.add_field(
                name=f"❓ {question}",
                value=answer,
                inline=False
            )

        # ----------------------------------------------------
        # SEND TIL LEDELSEN
        # ----------------------------------------------------

        await channel.send(
            embed=embed,
            view=ReviewView(
                applicant_id=user.id,
                app_title=self.app_title,
                accepted_role_id=self.accepted_role_id
            )
        )


# ============================================================
# GEMMER HVOR ANSØGNINGEN SKAL SENDES
# ============================================================

APPLICATION_CHANNELS = {}


# ============================================================
# ADMIN OPSÆTNING
# ============================================================

class AdminConfigView(discord.ui.View):

    def __init__(
        self,
        app_title: str,
        app_desc: str,
        channel: discord.TextChannel,
        accepted_role: discord.Role | None
    ):

        super().__init__(timeout=900)

        self.app_title = app_title
        self.app_desc = app_desc
        self.channel = channel
        self.accepted_role = accepted_role
        self.questions = []

    # ========================================================
    # OPDATER OPSÆTNING
    # ========================================================

    async def update_message(
        self,
        interaction: discord.Interaction
    ):

        role_text = (
            self.accepted_role.mention
            if self.accepted_role
            else "Ingen rolle valgt"
        )

        embed = discord.Embed(
            title=f"⚙️ Opsætning: {self.app_title}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📢 Ansøgningskanal",
            value=self.channel.mention,
            inline=False
        )

        embed.add_field(
            name="🎖️ Rolle ved godkendelse",
            value=role_text,
            inline=False
        )

        embed.add_field(
            name="📝 Beskrivelse",
            value=self.app_desc,
            inline=False
        )

        questions_text = ""

        if self.questions:

            for i, question in enumerate(
                self.questions,
                1
            ):

                questions_text += (
                    f"**{i}.** {question}\n"
                )

        else:

            questions_text = "*Ingen spørgsmål endnu.*"

        embed.add_field(
            name=f"❓ Spørgsmål ({len(self.questions)}/12)",
            value=questions_text,
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    # ========================================================
    # TILFØJ SPØRGSMÅL
    # ========================================================

    @discord.ui.button(
        label="Tilføj Spørgsmål",
        style=discord.ButtonStyle.blurple
    )
    async def add_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if len(self.questions) >= 12:

            await interaction.response.send_message(
                "❌ Du kan maks have 12 spørgsmål!",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            AddQuestionModal(self)
        )

    # ========================================================
    # UDGIV
    # ========================================================

    @discord.ui.button(
        label="Færdig & Udgiv",
        style=discord.ButtonStyle.green
    )
    async def publish(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.questions:

            await interaction.response.send_message(
                "❌ Du skal tilføje mindst ét spørgsmål!",
                ephemeral=True
            )

            return

        # Gem kanal
        APPLICATION_CHANNELS[
            self.app_title
        ] = self.channel.id

        # ----------------------------------------------------
        # PUBLIC EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title=f"📋 {self.app_title}",
            description=self.app_desc,
            color=discord.Color.green()
        )

        embed.add_field(
            name="📨 Sådan ansøger du",
            value=(
                "Tryk på **Ansøg Her** nedenfor.\n"
                "Du modtager derefter spørgsmålene "
                "direkte i DM."
            ),
            inline=False
        )

        if self.accepted_role:

            embed.add_field(
                name="🎖️ Ved godkendelse",
                value=(
                    f"Du får rollen "
                    f"{self.accepted_role.mention}."
                ),
                inline=False
            )

        else:

            embed.add_field(
                name="🎖️ Ved godkendelse",
                value="Ingen automatisk rolle.",
                inline=False
            )

        embed.set_footer(
            text=(
                f"{len(self.questions)} spørgsmål • "
                f"Svares over DM"
            )
        )

        # ----------------------------------------------------
        # SEND I DEN VALGTE KANAL
        # ----------------------------------------------------

        await self.channel.send(
            embed=embed,
            view=ApplicationStartView(
                app_title=self.app_title,
                questions=self.questions.copy(),
                accepted_role_id=(
                    self.accepted_role.id
                    if self.accepted_role
                    else None
                )
            )
        )

        await interaction.response.edit_message(
            content=(
                f"✅ Ansøgningssystemet er udgivet i "
                f"{self.channel.mention}!"
            ),
            embed=None,
            view=None
        )

        self.stop()


# ============================================================
# TILFØJ SPØRGSMÅL MODAL
# ============================================================

class AddQuestionModal(discord.ui.Modal):

    def __init__(
        self,
        config_view: AdminConfigView
    ):

        super().__init__(
            title="Tilføj spørgsmål"
        )

        self.config_view = config_view

        self.question = discord.ui.TextInput(
            label="Spørgsmål",
            placeholder="F.eks. Hvor gammel er du?",
            required=True,
            max_length=150
        )

        self.add_item(
            self.question
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        self.config_view.questions.append(
            self.question.value
        )

        await self.config_view.update_message(
            interaction
        )


# ============================================================
# START OPSÆTNING
# ============================================================

class AdminSetupView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=600
        )

        self.channel = None
        self.role = None

    # ========================================================
    # VÆLG KANAL
    # ========================================================

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[
            discord.ChannelType.text
        ],
        placeholder="📢 Vælg ansøgningskanal",
        min_values=1,
        max_values=1
    )
    async def channel_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect
    ):

        self.channel = select.values[0]

        await interaction.response.send_message(
            f"✅ Ansøgningskanal valgt: "
            f"{self.channel.mention}",
            ephemeral=True
        )

    # ========================================================
    # VÆLG ROLLE
    # ========================================================

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="🎖️ Vælg rolle ved godkendelse (valgfrit)",
        min_values=0,
        max_values=1
    )
    async def role_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.RoleSelect
    ):

        if select.values:

            self.role = select.values[0]

            await interaction.response.send_message(
                f"✅ Rolle valgt: {self.role.mention}",
                ephemeral=True
            )

        else:

            self.role = None

            await interaction.response.send_message(
                "ℹ️ Ingen rolle valgt. "
                "Der gives ingen automatisk rolle.",
                ephemeral=True
            )

    # ========================================================
    # FORTSÆT
    # ========================================================

    @discord.ui.button(
        label="Fortsæt",
        style=discord.ButtonStyle.green
    )
    async def continue_setup(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.channel is None:

            await interaction.response.send_message(
                "❌ Du skal vælge en ansøgningskanal først!",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            AdminSetupModal(
                self.channel,
                self.role
            )
        )


# ============================================================
# NAVN + BESKRIVELSE
# ============================================================

class AdminSetupModal(discord.ui.Modal):

    def __init__(
        self,
        channel: discord.TextChannel,
        role: discord.Role | None
    ):

        super().__init__(
            title="Opret ansøgningsskema"
        )

        self.channel = channel
        self.role = role

        self.name_input = discord.ui.TextInput(
            label="Ansøgningens navn",
            placeholder="F.eks. Staff Ansøgning",
            required=True,
            max_length=100
        )

        self.desc_input = discord.ui.TextInput(
            label="Beskrivelse / information",
            placeholder="Skriv info eller krav...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(
            self.name_input
        )

        self.add_item(
            self.desc_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        role_text = (
            self.role.mention
            if self.role
            else "Ingen rolle valgt"
        )

        embed = discord.Embed(
            title=f"⚙️ Opsætning: {self.name_input.value}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📢 Kanal",
            value=self.channel.mention,
            inline=False
        )

        embed.add_field(
            name="🎖️ Rolle ved godkendelse",
            value=role_text,
            inline=False
        )

        embed.add_field(
            name="📝 Beskrivelse",
            value=self.desc_input.value,
            inline=False
        )

        embed.add_field(
            name="❓ Spørgsmål",
            value="*Ingen spørgsmål endnu.*",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=AdminConfigView(
                app_title=self.name_input.value,
                app_desc=self.desc_input.value,
                channel=self.channel,
                accepted_role=self.role
            ),
            ephemeral=True
        )


# ============================================================
# SLASH COMMAND
# ============================================================

@bot.tree.command(
    name="create_application",
    description="Opret et nyt ansøgningssystem."
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def create_application(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        "⚙️ **Opsæt dit ansøgningssystem**\n\n"
        "1. Vælg den kanal hvor ansøgninger skal modtages.\n"
        "2. Vælg eventuelt en rolle som gives ved godkendelse.\n"
        "3. Tryk **Fortsæt**.",
        view=AdminSetupView(),
        ephemeral=True
    )


# ============================================================
# FEJL
# ============================================================

@create_application.error
async def create_application_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ Du skal være administrator "
            "for at bruge denne kommando!",
            ephemeral=True
        )

    else:

        print(
            f"Fejl i /create_application: {error}"
        )

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ Der opstod en fejl.",
                ephemeral=True
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    if TOKEN == "INDSAET_DIN_NYE_TOKEN_HER":

        print(
            "❌ Du mangler at indsætte din bot-token."
        )

    else:

        bot.run(TOKEN)