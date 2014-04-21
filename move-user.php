<?php
$req_admin = TRUE;
$get_json = TRUE;
require("access.php");
set_json();
if (!isset($_GET['uid'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['uid']);
if (!is_array($json_data) || !isset($json_data['instance'])) {
	die_error(400, "Bad JSON - must be an object with instance.");
}
$new_instance = intval($json_data['instance']);
if ($new_instance < 1) {
	die_error(400, "Bad JSON - Bad instance.");
}
$qry = $db->prepare("UPDATE `Players` SET `Instance` = ? WHERE `UID` = ? AND `Admin` = 1");
if ($qry === FALSE || !$qry->bind_param("ii", $new_instance, $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
echo json_encode(array());
