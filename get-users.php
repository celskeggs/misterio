<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
set_json();
$users = array();
$qry = $db->prepare("SELECT `UID`, `Name`, `Avatar`, `Email`, `Admin`, `Instance` FROM `Players` WHERE `Instance`=? OR `Admin`=1 ORDER BY `UID`");
if ($qry === FALSE || !$qry->bind_param("i", $user_instance) || !$qry->execute() || !$qry->bind_result($query_uid, $query_name, $query_avatar, $query_email, $query_admin, $query_instance)) {
	die_error(500, "Server Error: Could not submit body query.");
}
while ($qry->fetch()) {
	$user = array('uid' => $query_uid, 'name' => utf8_encode($query_name), 'avatar' => $query_avatar, 'instance' => $query_instance);
	if ($user_admin) {
		$user['email'] = $query_email;
		$user['access'] = $query_admin ? true : false;
	}
	$users[] = $user;
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish body query.");
}
echo json_encode(array('instance' => $user_instance, 'uid' => $user_uid, 'access' => $user_admin ? true : false, 'data' => $users));
