#include "cbase.h"
#include "cdll_int.h"
#include "custom_commands.h"
#include "team.h"
#include "hl2mp/hl2mp_gamerules.h"

ConCommand drop_weapon("drop_weapon", DropCurrentWeapon, "Immediately drop active weapon to the ground.");
ConCommand change_team("change_team", ChangeTeam, "Change player team.");

void DropCurrentWeapon(const CCommand& args)
{
	CBasePlayer* pPlayer = ToBasePlayer(UTIL_GetCommandClient());

	if (!pPlayer)
		return;

	CBaseCombatWeapon* pWeapon = pPlayer->GetActiveWeapon();

	if (!pWeapon)
		return;

	pPlayer->Weapon_DropSlot(pWeapon->GetSlot());
}

void ChangeTeam(const CCommand& args) {
	CBasePlayer* pPlayer = ToBasePlayer(UTIL_GetCommandClient());

	if (!pPlayer)
		return;

	if(pPlayer->GetTeamNumber() == TEAM_REBELS)
		pPlayer->ChangeTeam(TEAM_COMBINE);
	else
		pPlayer->ChangeTeam(TEAM_REBELS);

	pPlayer->Respawn();
}