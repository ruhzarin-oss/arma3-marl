

params ["_units","_building"];

if (typeName _building == "STRING" && {_building == "cursortarget"}) then {
	_building = cursortarget;
};

private _bpc = ([_building] call MCSS_fnc_getLastBuildingPosIndex);
private _targets = [(side (_units select 0)),(sizeOf (typeOf _building)),"ENEMY",(position _building),["MAN"]] call MCSS_fnc_NearEntities;
private _outerBuildingPositions = [_building,0] call MCSS_fnc_getBoundingBox;

{
	if (_x getVariable ["A3C_CLEARING",false]) then {
		_units = _units - [_x];
	};
} foreach _units;

private _roofSensitive = false;

{
	if (((getPosATL _x) select 2) > 7) then {
		if (["barracks",typeOf _building] call BIS_fnc_instring) then {
			if !(["ruin",typeOf _building] call BIS_fnc_instring) then {
				_roofSensitive = true;
			};
		};
	};
} foreach _targets;

if (["Land_jbad_House6",typeOf _building] call BIS_fnc_instring) then {
	_roofSensitive = true;
};

private _fnc_createBuddyTeams = {
	//-- bundle units into groups of 2
	params ["_assignedUnits"];

	private _returnArray = [];

	while {(count _assignedUnits) > 0} do {
		private _subArray = [];
		_subArray pushBack (_assignedUnits select 0);

		if (count _assignedUnits > 1) then {
			_subArray pushBack (_assignedUnits select 1);
		};

		_assignedUnits = _assignedUnits - _subArray;
		_returnArray pushBack _subArray;
	};

	_returnArray;
};

private _fnc_assignRoomPoses = {
	//-- assign roomPoses to unitArray
	params ["_units","_building","_roomData","_radius"];

	private _roomPoses = _roomData select 0;

	private _roomID = +(_roomPoses select 0);
	private _roomPosAmount = ((count _roomPoses) - 2) max 0;

	while {(count _roomPoses) > _roomPosAmount} do {
		{
			//~~ the last two building poses in room need an identical main-markername so that units will wait for one another!
			if ((count _roomPoses) == _roomPosAmount) exitWith {};

			private _roomPosATL = if ((typeName (_roomPoses select 0)) == "SCALAR") then {
				_building buildingPos (_roomPoses select 0)
			} else {
				(_roomPoses select 0)
			};

			private _data = _x getVariable ["A3C_PLOT",[]];
			private _markerName = format ["A3C_BUILDINGMARKER_%1_Room_%2",str _building,_roomID];
			private _wp = [
				[_roomPosATL,_roomPosATL getPos [50,0]],
				[_markerName,"",""],
				["NONE",nil],
				["NONE",nil],
				["UP","AUTO"],
				[[0,false]],
				false,
				0,
				-1,
				25,
				-1,
				3 //-- radius
			];

			_data pushBack _wp;
			_x setvariable ["A3C_PLOT",_data,true];
			_roomPoses deleteAt 0;
		} foreach _units;
	};
};

if !(isDedicated) then {
	_units = [_units,[],{vehicle _x distance2D (_building buildingPos 0)},"ASCEND"] call BIS_fnc_sortBy; //-- script gets stuck here!
	{_x setVariable ["A3C_PLOT",[],true]} foreach _units;
};

//-- create buddy Teams and array of rooms
private _buddyArrays = [_units] call _fnc_createBuddyTeams;
private _roomArrays = [_building,_bpC,_roofSensitive] call A3C_main_fnc_buildingCreateRooms;

if ({player == leader group _x} count _units == count _units) then {
	[_units,true,false] call A3C_ai_shared_fnc_cancelUnitPlot; //~~ ideally: _busyUnits only! || some issue with HC units not resetting A3C_PLOT
} else {
	{
		if (count (_x getvariable ["A3C_PLOT",[]]) > 0) then {
			_x setvariable ["A3C_ABORT_Data",[true,false],true];
		};
	} foreach _units;

	waitUntil {{count (_x getVariable ["A3C_PLOT",[]]) > 0} count _units == 0};
};

while {({(count(_x getvariable ["A3C_PLOT",[]])) > 0} count _units) > 0} do {sleep 0.1}; //~~ ideally: _clearingUnits

sleep 0.5;

//-- add entry wp to each unit
{
	if (_forEachIndex < (count _roomArrays)) then {
		private _entryPosition = _building buildingPos 0;
		private _data = _x getVariable ["A3C_PLOT",[]];
		private _wp = [
			[_entryPosition,_entryPosition getPos [50,0]],
			["","",""],
			["NONE",nil],
			["NONE",nil],
			["UP","AUTO"],
			[[0,false]],
			false,
			0,
			-1,
			25,
			-1,
			7
		];

		_data pushBack _wp;
		_x setvariable ["A3C_PLOT",_data,true];
	} else {
		if (count _outerBuildingPositions > 0) then {
			private _edgePos = (_outerBuildingPositions select 0);
			private _guardDir = [_building, _edgePos] call BIS_fnc_dirTo;
			private _guardLookPos = [_edgePos,50,_guardDir] call BIS_fnc_relPos;

			[_x,_edgePos] remoteExec ["doMove",_x];
			[_x,_guardLookPos] remoteExec ["lookAt",_x];

			_outerBuildingPositions deleteAt 0;
		};
	};
} foreach _units;

private _originalRooms = +(_roomArrays);

{
	private _leader = _x select 0;
	private _leaderZ = (getPosATL _leader) select 2;
	private _buildingEntryPos = _building buildingPos 0;
	private _roomArrays1 = +_roomArrays;

	private _sameFloorRooms = _roomArrays1 select {
		private _roomBpos = (_x select 0) select 0;
		private _roomZ = (_building buildingPos _roomBpos) select 2;

		(abs (_roomZ - _leaderZ)) < 1
	};

	if (count _sameFloorRooms > 0) then {
		_roomArrays1 = _sameFloorRooms;
	};

	_roomArrays1 = [
		_roomArrays1,
		[],
		{
			private _doorPositions = _x select 1;
			private _test = if (count _doorPositions > 0) then {
				_doorPositions select 0
			} else {
				_building buildingPos ((_x select 0) select 0)
			};

			_test distance _buildingEntryPos
		},
		"ASCEND"
	] call BIS_fnc_sortBy;

	if (count _roomArrays1 > 0) then {
		private _nextRoom = _roomArrays1 select 0;
		_roomArrays = _roomArrays - [_nextRoom];
		[_x,_building,_nextRoom,3] call _fnc_assignRoomPoses;
	};
} foreach _buddyArrays;

//--execute assigned data

//-- individual unit monitor
{
	private _wpData = (_x getvariable "A3C_PLOT");
	_x setVariable ["A3C_CLEARING",true,true];

	if (count _wpData > 0) then {
		if (_forEachIndex > 0) then {
			[_x,_units select (_forEachIndex -1)] execFSM "A3C_CORE\FSM\A3C_AI_CLEAR_SPEED.fsm";
		};

		private _scr = ([_x,_wpData] spawn A3C_ai_shared_fnc_actionExecuteUnitPlot);

		///// --------- SPAWN FOR PARALLEL UNIT BEHAVIOR
		[_x,_building,_units] spawn {
			params ["_unit","_building","_units","_bPosArray"];

			private _resetDanger = if !(_unit in A3C_AutoCombatDisabledUnits) then {true} else {false};
			private _pauseCounter = 0;

			while {_unit getVariable "A3C_CLEARING"} do {
				[_unit,"AUTOCOMBAT"] remoteExec ["disableAI",_unit];

				if (!alive _unit) exitWith {
					_unit setVariable ["A3C_CLEARING",false,true];
				};

				[_unit,"UP"] remoteExec ["setUnitPos",_unit];

				private _target = objNull;
				private _targets = [(side _unit),(sizeOf (typeOf _building)),"ENEMY",(position _building),["MAN"]] call MCSS_fnc_NearEntities;
				_targets = [_targets,[],{_x distance _unit},"ASCEND"] call BIS_fnc_sortBy;

				private _unitZ = (getPosATL _unit) select 2;

				_targets = _targets select {
					private _targetZ = (getPosATL _x) select 2;
					private _sameHeight = (abs (_unitZ - _targetZ)) <= 1.5;
					_sameHeight
				};

				if (count _targets > 0) then {
					_target = _targets select 0; //-- '_target' is specifically the UNIT's target. not to be confused with '_t'
				};

				private _doFire = false;

				private _unitEyePos = eyePos _unit;
				private _otherUnits = _units - [_unit];

				{
					private _t = _x;
					private _targetEyePos = eyePos _t;
					private _hasLOS = !(_building in lineIntersectsWith [_unitEyePos,_targetEyePos,_unit,_t,false]);

					if (_hasLOS) then {
						_doFire = true;
						_target = _t;
						A3C_ENGAGEDTARGETS pushBackUnique _target;
					} else {
						if !(_t in A3C_ENGAGEDTARGETS) then {
							
						} else {
							private _isSeenByOtherUnit = (_otherUnits findIf {
								private _u = _x;
								!(_building in lineIntersectsWith [eyePos _u,_targetEyePos,_u,_t,false])
							}) != -1;

							if (!_isSeenByOtherUnit) then {
								A3C_ENGAGEDTARGETS = A3C_ENGAGEDTARGETS - [_t];
							};
						};
					};
				} foreach _targets;

				if (!isNull _target) then {
					
				};

				if (_doFire) then {
					
					
					sleep 2;
				};

				_targets = [(side _unit),(sizeOf (typeOf _building)),"ENEMY",(position _building),["MAN"]] call MCSS_fnc_NearEntities;

				if (speed _unit == 0) then {
					if !(_unit getVariable ["A3C_ClearingPause",false]) then {
						_pauseCounter = _pauseCounter + 0.1;

						if (_pauseCounter >= 30) then {
							_pauseCounter = 0;

							{
								private _t = _x;

								if (_t distance (expectedDestination _unit select 0) < 1) then {
									{
										[_t,_x] remoteExec ["enableAI",_t];
									} foreach ["MOVE","PATH"]; //-- unit stuck may have something to do with enemy unit blocking path

									{
										[_t,_x] remoteExec ["doMove",_t];
										[_t,_x] remoteExec ["moveTo",_t];
									} foreach [_building buildingPos 0];
								};
							} foreach _targets;
						};
					};
				};

				sleep 0.1;
			};

			[_unit,"AUTO"] remoteExec ["setUnitPos",_unit];
			[_unit,-1] remoteExec ["forceSpeed",_unit];

			//-- loop over: unit is no longer clearing!
			if (_resetDanger) then {
				[_unit,"AUTOCOMBAT"] remoteExec ["enableAI",_unit];
			};
		};
	};

	sleep 2;
} foreach _units;

///// --------------------------------------- /////
///// ----------- P A R A L L E L ----------- /////
///// ----------- BUDDY WP DISTRO ----------- /////
///// --------------------------------------- /////
//-- buddyTeam monitor and room assigner
[_units, _buddyArrays,_building,_roomArrays,_originalRooms,_fnc_assignRoomPoses] spawn {
	params ["_units","_buddyArrays","_building", "_roomArrays","_originalRooms","_fnc_assignRoomPoses"];

	private _group = group (_units select 0);
	private _currentWaypoint = currentWaypoint _group;
	private _waypointPos = +(waypointPosition [_group,_currentWaypoint]);

	private _fnc_breakFromOrders = {
		params ["_unit","_building"];

		private _bbox = [_building,0] call MCSS_fnc_getBoundingBox;
		private _area = [((_bbox select 0) distance2d (_bbox select 1)) / 2,((_bbox select 1) distance2d (_bbox select 2)) / 2];
		private _expDest = (expectedDestination _unit) select 0;
		private _result = _expDest inArea [position _building, _area select 0, _area select 1, getDir _building, false];

		if (_result) then {
		};

		_result
	};

	//-- Q: Why would the script run without any roomarray entries left?
	//-- A: wait for units to complete orders, or waypoint will complete on executing last order
	while {
		private _cwp = currentWaypoint _group;

		(_cwp == _currentWaypoint && {(waypointPosition [_group,_cwp]) isEqualTo _waypointPos}) &&
		{
			(count _roomArrays > 0) OR
			{
				{count (_x getVariable ["A3C_PLOT",[]]) > 0} count _units > 0
			}
		}
	} do {
		A3C_ENGAGEDTARGETS = A3C_ENGAGEDTARGETS select {
			!(isNull _x) && {alive _x}
		};

		{
			private _team = _x;
			private _teamIndex = _forEachIndex;
			private _exitLoop = false;

			{
				private _unit = _x;
				private _unitAlive = alive _unit;

				if (
					!_unitAlive
					OR
					{
						isPlayer leader group _unit
						&&
						{
							(currentCommand _unit == "STOP")
							OR
							{
								["formation",(expectedDestination _unit) select 1] call MCSS_fnc_isInString
							}
						}
					}
				) then {
					_exitLoop = true;

					if (count (_unit getVariable ["A3C_PLOT",[]]) > 0) then {
						_unit setvariable ["A3C_ABORT_Data",[true,false],true];
					};

					systemchat 'error 1 clearb / or unit is dead';

					_unit setVariable ["A3C_CLEARING",false,true];
					_team = _team - [_unit];
					_buddyArrays set [_teamIndex, _team];

					if (!_unitAlive) then {
						private _closestBpos = ([getposATL _unit,_building] call A3C_main_fnc_findClosestBpos) select 0;
						private _matchingRooms = _originalRooms select {
							_closestBpos in _x
						};

						if (count _matchingRooms > 0) then {
							_roomArrays pushBackUnique (_matchingRooms select ((count _matchingRooms) - 1));
						};
					};
				};
			} foreach _team;

			if (_exitLoop) exitWith {
			};

			if ((_team findIf {alive _x}) == -1) then {
				_buddyArrays = _buddyArrays - [_team];
			} else {
				if ((_team findIf {count (_x getVariable ["A3C_PLOT",[]]) > 0}) == -1) then {
					if (count _roomArrays > 0) then {
						private _leader = objNull;

						{
							if (alive _x) exitWith {
								_leader = _x;
							};
						} foreach _team;

						private _leaderZ = (getPosATL _leader) select 2;
						private _roomArrays1 = +_roomArrays;

						private _sameFloorRooms = _roomArrays1 select {
							private _roomZ = (_building buildingPos ((_x select 0) select 0)) select 2;
							(abs (_roomZ - _leaderZ)) < 1
						};

						if (count _sameFloorRooms > 0) then {
							_roomArrays1 = _sameFloorRooms;
						};

						_roomArrays1 = [_roomArrays1,[],{
							private _doorPoses = _x select 1;
							private _test = if (count _doorPoses > 0) then {
								_doorPoses select 0
							} else {
								_building buildingPos ((_x select 0) select 0)
							};

							_test distance _leader
						},"ASCEND"] call BIS_fnc_sortBy; //-- assign next room by closest door

						private _nextRoom = _roomArrays1 select 0;

						if (!isNil '_nextRoom') then {
							_roomArrays = _roomArrays - [_nextRoom];
							[_x,_building,_nextRoom,3] call _fnc_assignRoomPoses;
							sleep 0.1;

							{
								private _scr = ([_x,(_x getvariable "A3C_PLOT")] spawn A3C_ai_shared_fnc_actionExecuteUnitPlot);
							} foreach _team;
						};
					};
				};
			};
		} foreach _buddyArrays;

		private _exit = true;

		{
			private _team = _x select {alive _x};

			{
				if (count (_x getVariable ["A3C_PLOT",[]]) > 0) then {
					_exit = false;
				} else {
				};
			} foreach _team;
		} foreach _buddyArrays;

		if (_exit) exitWith {
		};

		sleep 1;
	};

	{
		{
			_x setVariable ["A3C_CLEARING",false,true];
			_x setVariable ["A3C_PLOT",[],true];
		} foreach _x;
	} foreach _buddyArrays;
};