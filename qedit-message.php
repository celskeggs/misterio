<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['id']) || !isset($_GET['operation'])) {
	die_error(400, "Should have id!");
}
$operation = $_GET['operation'];
$target_id = intval($_GET['id']);
if ($operation !== "finalize") {
	die_error(400, "Unrecognized command");
}
$qry = $db->prepare("UPDATE `Posts` SET `IsFinish` = !`IsFinish` WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
echo json_encode(array());
