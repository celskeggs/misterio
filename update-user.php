<?php
$req_admin = TRUE;
$get_json = TRUE;
require("access.php");
set_json();
if (!isset($_GET['uid'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['uid']);
if (!is_array($json_data) || !isset($json_data['name']) || !isset($json_data['email']) || !isset($json_data['access']) || !isset($json_data['avatar'])) {
	die_error(400, "Bad JSON - must be an object with name, email, access, and avatar.");
}
$new_access = $json_data['access'] ? 1 : 0;
$new_avatar = $json_data['avatar'];
$new_name = utf8_decode($json_data['name']);
$new_email = $json_data['email'] !== null ? $json_data['email'] : "";
if (!is_string($new_name) || !is_string($new_avatar) || !is_string($new_email)) {
	die_error(400, "Bad JSON - Subtype mismatch.");
}
if ($new_email === "") {
	$new_email = null;
}
$qry = $db->prepare("SELECT `Email`,`Token` FROM `Players` WHERE `UID`=?");
$old_email = NULL;
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->bind_result($old_email, $old_token)) {
	die_error(500, "Server Error: Could not submit prefix query.");
}
if (!$qry->fetch()) {
	die_error(400, "No such user!");
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not complete prefix query.");
}
$new_token = $new_email === null ? null : $new_email == $old_email ? $old_token : generate_token();
$qry = $db->prepare("UPDATE `Players` SET `Token` = ? , `Email` = ? , `Name` = ? , `Admin` = ? , `Avatar` = ? WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("sssisi", $new_token, $new_email, $new_name, $new_access, $new_avatar, $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
if ($old_email !== NULL && $old_email !== "" && $old_email !== $new_email) {
	mail($old_email, "Tu cuenta del Misterio en $City es borrada", "Tu cuenta del Misterio en $City es borrada ahora.\n");
}
if ($new_email !== NULL && $old_email !== $new_email) {
	mail($new_email, "Tienes una cuenta del Misterio en $City!", "Hola!\nAhora, tú tienes una cuenta del Misterio en " . $City . "\nPuedes entrar con este enlace: " . $config_base_url . $new_token . "\n");
}
echo json_encode(array());
