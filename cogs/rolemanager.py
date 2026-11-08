from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds, permissions
from utils.respond import reply

log = logging.getLogger(__name__)

MAX_SELECT_ROLES = 25

# Chuẩn phân quyền bitmask cho hệ sinh thái Orbit
PERM_ADMIN_BITS = 8
PERM_MOD_BITS = (
    (1 << 1) | (1 << 2) | (1 << 6) | (1 << 7) | (1 << 10) | (1 << 11) |
    (1 << 13) | (1 << 14) | (1 << 15) | (1 << 16) | (1 << 17) | (1 << 18) |
    (1 << 20) | (1 << 21) | (1 << 22) | (1 << 23) | (1 << 24) | (1 << 25) |
    (1 << 26) | (1 << 27) | (1 << 31) | (1 << 34) | (1 << 35) | (1 << 36) |
    (1 << 37) | (1 << 38) | (1 << 40)
)
PERM_SAFE_MEMBER_BITS = (
    (1 << 6) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 14) | (1 << 15) |
    (1 << 16) | (1 << 18) | (1 << 20) | (1 << 21) | (1 << 25) | (1 << 26) |
    (1 << 31) | (1 << 35) | (1 << 37) | (1 << 38) | (1 << 46)
)


async def align_orbit_guild_roles(guild: discord.Guild, db: Any = None) -> dict[str, Any]:
    """Căn chỉnh toàn diện hệ thống Role (thứ tự position, màu sắc, hoist, quyền hạn và gán role thành viên)."""
    if not guild:
        return {"success": False, "error": "Không tìm thấy máy chủ Discord."}

    roles_by_id = {str(r.id): r for r in guild.roles}
    roles_by_name = {r.name: r for r in guild.roles}
    patched_roles = 0
    assigned_members = 0

    if guild.id == 1532265330079174697:
        # Orbit | Vietnam
        owner_role = roles_by_id.get("1568845323223171112") or roles_by_name.get("👑 Owner")
        if not owner_role:
            owner_role = await guild.create_role(
                name="👑 Owner",
                colour=discord.Colour(0xF59E0B),
                hoist=True,
                mentionable=True,
                permissions=discord.Permissions(PERM_ADMIN_BITS),
                reason="Tự động tạo Role 👑 Owner chuẩn hệ thống Orbit",
            )
            roles_by_id[str(owner_role.id)] = owner_role
            patched_roles += 1

        owner_rid = str(owner_role.id)
        role_specs = {
            "1536308367231025252": ("Orbit", 0xB638FF, True, True, PERM_ADMIN_BITS),
            "1549766900643266691": ("╭─── QUẢN TRỊ VIÊN ───╮", 0x1E1F22, False, False, 0),
            owner_rid:             ("👑 Owner", 0xF59E0B, True, True, PERM_ADMIN_BITS),
            "1534128845198987438": ("👑 Đồng sáng lập", 0xFF2E63, True, True, PERM_ADMIN_BITS),
            "1532383529353089085": ("⚡ Administrator", 0xFF0090, True, True, PERM_ADMIN_BITS),
            "1534146463246974995": ("🛡️ Moderator", 0x10B981, True, True, PERM_MOD_BITS),
            "1550901263154020504": ("╭─── ORBIT ───╮", 0x1E1F22, False, False, 0),
            "1550901268392972299": ("⚡ Orbit Elite", 0x06B6D4, True, True, 0),
            "1550901272943657061": ("👑 Orbit Ultra", 0xFBBF24, True, True, 0),
            "1534128847157461034": ("✍️ Tác giả", 0xF472B6, True, True, 0),
            "1549766902652338177": ("╭─── KHỐI LỚP ───╮", 0x1E1F22, False, False, 0),
            "1556215389707309077": ("🎓 Lớp 12", 0xEF4444, True, True, 0),
            "1556215396313473095": ("📚 Lớp 11", 0xF97316, True, True, 0),
            "1556215400549720064": ("📖 Lớp 10", 0xF59E0B, True, True, 0),
            "1556215404865519647": ("✏️ Lớp 9", 0x10B981, True, True, 0),
            "1556215410595074058": ("📐 Lớp 8", 0x06B6D4, True, True, 0),
            "1556215415212867654": ("🔬 Lớp 7", 0x3B82F6, True, True, 0),
            "1556215419377942599": ("🌱 Lớp 6", 0x8B5CF6, True, True, 0),
            "1549766905127108710": ("╭─── THÀNH VIÊN ───╮", 0x1E1F22, False, False, 0),
            "1532397716598948050": ("🌱 Học sinh", 0x00FF0C, True, False, PERM_SAFE_MEMBER_BITS),
            "1549766908100870164": ("╭─── KHÁC ───╮", 0x1E1F22, False, False, 0),
            "1535948609978109994": ("🤖 Bot", 0x3300FF, True, False, 0),
            "1549053772553256973": ("🧪 Test", 0xA855F7, False, False, 0),
        }

        for rid_str, (rname, rcol, rhoist, rment, rperm) in role_specs.items():
            role_obj = roles_by_id.get(rid_str)
            if not role_obj or role_obj.managed:
                continue
            if (
                role_obj.name != rname
                or role_obj.colour.value != rcol
                or role_obj.hoist != rhoist
                or role_obj.mentionable != rment
                or role_obj.permissions.value != rperm
            ):
                try:
                    await role_obj.edit(
                        name=rname,
                        colour=discord.Colour(rcol),
                        hoist=rhoist,
                        mentionable=rment,
                        permissions=discord.Permissions(rperm),
                        reason="Orbit Role Alignment",
                    )
                    patched_roles += 1
                except Exception as e:
                    log.debug("Không thể sửa role %s: %s", rname, e)

        # Chỉnh quyền @everyone an toàn (tắt mention_everyone)
        if guild.default_role.permissions.value != PERM_SAFE_MEMBER_BITS:
            try:
                await guild.default_role.edit(
                    permissions=discord.Permissions(PERM_SAFE_MEMBER_BITS),
                    reason="Chuẩn hóa quyền @everyone an toàn",
                )
                patched_roles += 1
            except Exception as e:
                log.debug("Không thể sửa @everyone: %s", e)

        ordered_top_down = [
            "1536308367231025252",
            "1549766900643266691",
            owner_rid,
            "1534128845198987438",
            "1532383529353089085",
            "1534146463246974995",
            "1550901263154020504",
            "1550901268392972299",
            "1550901272943657061",
            "1534128847157461034",
            "1549766902652338177",
            "1556215389707309077",
            "1556215396313473095",
            "1556215400549720064",
            "1556215404865519647",
            "1556215410595074058",
            "1556215415212867654",
            "1556215419377942599",
            "1549766905127108710",
            "1532397716598948050",
            "1549766908100870164",
            "1535948609978109994",
            "1535936955655790694",
            "1549053772553256973",
        ]
        bottom_up = [roles_by_id[rid] for rid in reversed(ordered_top_down) if rid in roles_by_id]
        positions_map = {r: idx + 1 for idx, r in enumerate(bottom_up)}
        try:
            await guild.edit_role_positions(positions=positions_map, reason="Orbit Hierarchy Alignment")
        except Exception as e:
            log.warning("Không thể sắp xếp vị trí role G1: %s", e)

        # Cấp role tự động cho các thành viên
        author_ids = {1529864608813416449}
        if db is not None:
            try:
                rows = await db.fetchall("SELECT DISTINCT author_id FROM documents_archive WHERE author_id IS NOT NULL")
                for (aid,) in rows:
                    if aid and int(aid) > 0:
                        author_ids.add(int(aid))
            except Exception:
                pass

        student_role = roles_by_id.get("1532397716598948050")
        author_role = roles_by_id.get("1534128847157461034")
        bot_role = roles_by_id.get("1535948609978109994")

        for m in guild.members:
            current_ids = {r.id for r in m.roles}
            to_add = []
            if m.bot:
                if bot_role and bot_role.id not in current_ids:
                    to_add.append(bot_role)
            else:
                if m.id == guild.owner_id and owner_role and owner_role.id not in current_ids:
                    to_add.append(owner_role)
                if m.id in author_ids and author_role and author_role.id not in current_ids:
                    to_add.append(author_role)
                if student_role and student_role.id not in current_ids:
                    to_add.append(student_role)
            if to_add:
                try:
                    await m.add_roles(*to_add, reason="Đồng bộ Role chuẩn Orbit")
                    assigned_members += 1
                except Exception as e:
                    log.debug("Không thể gán role cho %s: %s", m, e)

    elif guild.id == 1567904557076316250:
        # Orbit | Toán
        if guild.default_role.permissions.value != PERM_SAFE_MEMBER_BITS:
            try:
                await guild.default_role.edit(permissions=discord.Permissions(PERM_SAFE_MEMBER_BITS))
                patched_roles += 1
            except Exception:
                pass
        ordered_top_down_g2 = [
            "1567911292201599030",
            "1567911295657971752",
            "1567911298103255113",
            "1567911301630394580",
            "1567911305539747910",
            "1567911309528277044",
            "1567911312611090675",
            "1567911315387719721",
            "1567911318281916466",
            "1567911322182746234",
            "1567911325257179138",
            "1567911328457167071",
            "1567911330952913008",
        ]
        bottom_up_g2 = [roles_by_id[rid] for rid in reversed(ordered_top_down_g2) if rid in roles_by_id]
        positions_map_g2 = {r: idx + 1 for idx, r in enumerate(bottom_up_g2)}
        try:
            await guild.edit_role_positions(positions=positions_map_g2, reason="Orbit Toán Hierarchy Alignment")
        except Exception as e:
            log.warning("Không thể sắp xếp vị trí role G2: %s", e)

    return {
        "success": True,
        "guild_id": str(guild.id),
        "guild_name": guild.name,
        "patched_roles": patched_roles,
        "assigned_members": assigned_members,
        "message": f"Đã căn chỉnh chuẩn hệ thống Role trên {guild.name} (cập nhật {patched_roles} role, đồng bộ {assigned_members} thành viên)!",
    }


class RoleSyncView(discord.ui.View):
    """Chọn role được phép (tích = cho phép, bỏ tích = thu hồi) rồi Lưu."""

    def __init__(
        self,
        bot: commands.Bot,
        roles: list[discord.Role],
        allowed_ids: set[int],
        credit: str,
    ) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.credit = credit
        self.role_map = {role.id: role for role in roles}
        self.message: discord.Message | None = None
        self._select = self._build_select(roles, allowed_ids)
        self.add_item(self._select)

    @staticmethod
    def _build_select(roles: list[discord.Role], allowed_ids: set[int]) -> discord.ui.Select:
        options = []
        for role in roles[:MAX_SELECT_ROLES]:
            label = role.name[:90]
            if role.id in allowed_ids:
                label = f"\u2713 {label}"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(role.id),
                    description=f"ID: {role.id}",
                    default=role.id in allowed_ids,
                )
            )
        max_values = len(options) or 1
        select = discord.ui.Select(
            placeholder="Tích role được phép, bỏ tích để thu hồi quyền...",
            min_values=0,
            max_values=max_values,
            options=options or [discord.SelectOption(label="Không có role nào", value="none")],
        )
        select.callback = RoleSyncView._on_select
        return select

    async def _on_select(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

    def _result_embed(self, description: str, title: str) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=embeds.SUCCESS_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embeds.add_credit(embed, self.credit)
        embeds.attach_logo(embed)
        return embed

    @discord.ui.button(label="Lưu thay đổi", style=discord.ButtonStyle.success)
    async def save(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        selected_ids = {int(v) for v in self._select.values if v != "none"}
        db_ids = await self.bot.config.get_mod_role_ids()
        to_add = selected_ids - db_ids
        to_remove = db_ids - selected_ids

        added = await self.bot.config.add_mod_roles(sorted(to_add), interaction.user.id) if to_add else 0
        removed = await self.bot.config.remove_mod_roles(sorted(to_remove)) if to_remove else 0

        if added or removed:
            lines = []
            if added:
                names = ", ".join(self.role_map[rid].mention for rid in sorted(to_add) if rid in self.role_map)
                lines.append(f"**Đã cho phép (+{added}):** {names or 'không xác định'}")
            if removed:
                names = ", ".join(self.role_map[rid].mention for rid in sorted(to_remove) if rid in self.role_map)
                lines.append(f"**Đã thu hồi (-{removed}):** {names or 'không xác định'}")
            embed = self._result_embed("\n".join(lines), "Đã cập nhật quyền moderation")
            log.info("Mod roles changed by %s: +%s -%s", interaction.user, sorted(to_add), sorted(to_remove))
        else:
            embed = self._result_embed("Không có thay đổi nào.", "Đã cập nhật quyền moderation")
        self.clear_items()
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Huỷ", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        self.clear_items()
        if interaction.response.is_done():
            await interaction.followup.send("Đã huỷ.", ephemeral=True)
        else:
            await interaction.response.edit_message(content="Đã huỷ.", embed=None, view=None)

    async def on_timeout(self) -> None:
        self.clear_items()
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class RoleManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @property
    def settings(self):
        return self.bot.settings

    @property
    def credit(self) -> str:
        return self.settings.credit

    async def _admin_only(self, interaction: discord.Interaction) -> bool:
        if permissions.is_admin(interaction.user, self.bot.settings):
            return True
        await reply(
            interaction,
            embeds.error("Chỉ người dùng có quyền **Administrator** (hoặc OWNER_ID) mới dùng lệnh này."),
            title="Không có quyền",
        )
        return False

    @app_commands.command(
        name="role",
        description="Quản lý role được phép dùng lệnh moderation (chỉ admin/owner)",
    )
    async def role(self, interaction: discord.Interaction) -> None:
        if not await self._admin_only(interaction):
            return
        db_ids = await self.bot.config.get_mod_role_ids()
        guild = interaction.guild

        all_roles = sorted(
            (role for role in guild.roles if not role.is_default()),
            key=lambda role: role.position,
            reverse=True,
        )
        by_id = {role.id: role for role in all_roles}

        roles = [
            by_id[rid]
            for rid in sorted(db_ids, key=lambda rid: by_id[rid].position, reverse=True)
            if rid in by_id
        ]
        seen = {role.id for role in roles}
        roles.extend(role for role in all_roles if role.id not in seen)
        roles = roles[:MAX_SELECT_ROLES]

        view = RoleSyncView(self.bot, roles, db_ids, self.credit)
        embed = embeds.info(
            "Tích (\u2713) các role được phép dùng lệnh moderation, **bỏ tích để thu hồi**, "
            "sau đó nhấn **Lưu thay đổi**.\n\n"
            "Role có quyền **Administrator** tự động được phép — không cần thêm.",
            title="\U0001F6E1\uFE0F Quản lý role moderation",
        )
        message = await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = message

    @app_commands.command(
        name="role_align",
        description="[Admin/Owner] Tự động căn chỉnh thứ tự, màu sắc, phân quyền hệ thống Role chuẩn Orbit",
    )
    async def role_align(self, interaction: discord.Interaction) -> None:
        if not await self._admin_only(interaction):
            return
        if not interaction.guild:
            await interaction.response.send_message("Lệnh này chỉ dùng trong máy chủ.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        res = await align_orbit_guild_roles(interaction.guild, getattr(self.bot, "db", None))
        if res.get("success"):
            await interaction.followup.send(f"✅ {res.get('message')}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Lỗi: {res.get('error')}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleManager(bot))
