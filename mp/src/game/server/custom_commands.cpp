#include "cbase.h"
#include "cdll_int.h"
#include "custom_commands.h"

ConCommand drop_weapon( "drop_weapon", DropCurrentWeapon, "Immediately drop active weapon to the ground." );

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