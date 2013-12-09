<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
$users = array();
$qry = $db->prepare("SELECT `UID`, `Name`, `Avatar`, `Email`, `Admin` FROM `Players` ORDER BY `UID`");
if ($qry === FALSE || !$qry->execute() || !$qry->bind_result($query_uid, $query_name, $query_avatar, $query_email, $query_admin)) {
	die_error(500, "Server Error: Could not submit body query.");
}
while ($qry->fetch()) {
	$user = array('uid' => $query_uid, 'name' => $query_name, 'avatar' => $query_avatar);
	if ($user_admin) {
		$user['email'] = $query_email;
		$user['access'] = $query_admin ? true : false;
	}
	$users[] = $user;
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish body query.");
}
echo json_encode(array('uid' => $user_uid, 'access' => $user_admin ? true : false, 'data' => $users));
