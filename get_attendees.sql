SELECT meta_attendee.post_id, contact, airtable_id, sur FROM 
	(SELECT post_id, meta_value AS contact FROM wp_gvxun9_postmeta
		WHERE meta_key = "_tribe_attendee_activity_log") 
		AS meta_attendee 
	LEFT JOIN (SELECT post_id, CAST(meta_value AS UNSIGNED) AS event_id 
				FROM wp_gvxun9_postmeta 
				WHERE meta_key = "_tribe_rsvp_event") AS meta_event
		ON meta_attendee.post_id = meta_event.post_id	
		
	LEFT JOIN (SELECT post_id, meta_value AS airtable_id
				FROM wp_gvxun9_postmeta 
				WHERE meta_key = "_ecp_custom_41" AND meta_value NOT IN ("","None")) 
				AS meta_airtable
	ON meta_airtable.post_id = meta_event.event_id
	
	LEFT JOIN (SELECT post_id, meta_value AS sur
				FROM wp_gvxun9_postmeta wgp
				WHERE meta_key = "_tribe_tickets_meta")
				AS meta_sur
	ON meta_attendee.post_id = meta_sur.post_id