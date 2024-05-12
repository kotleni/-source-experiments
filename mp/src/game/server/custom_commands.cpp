#include "cbase.h"
#include "cdll_int.h"
#include "custom_commands.h"
#include "team.h"
#include "hl2mp/hl2mp_gamerules.h"
#include "viewport_panel_names.h"

ConCommand drop_weapon("drop_weapon", DropCurrentWeapon, "Immediately drop active weapon to the ground.");
ConCommand change_team("change_team", ChangeTeam, "Change player team.");
ConCommand test_menu1("test_menu1", TestIt, "");

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

void TestIt() {
	CBasePlayer* pPlayer = ToBasePlayer(UTIL_GetCommandClient());

	const ConVar* hostname = cvar->FindVar("hostname");
	const char* title = (hostname) ? hostname->GetString() : "MESSAGE OF THE DAY";

	KeyValues* data = new KeyValues("data");
	data->SetString("title", title);		// info panel title
	data->SetString("type", "1");			// show userdata from stringtable entry
	data->SetString("msg", "motd");		// use this stringtable entry
	//data->SetBool("unload", sv_motd_unload_on_dismissal.GetBool());

	pPlayer->ShowViewPortPanel( PANEL_TEAM, true, data );

	data->deleteThis();
}