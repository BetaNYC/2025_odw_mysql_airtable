SELECT name_t.post_id , name, email, airtable_id, zoom_link, 
	other_link, eventName, eventDt, eventLocation, eventUrl, survey, ticket_name, ticket_time FROM 
	(SELECT post_id, meta_value as Name FROM wp_f729y5_postmeta
		WHERE meta_key = "_tribe_rsvp_full_name") as name_t
	LEFT JOIN (SELECT post_id, meta_value as email FROM wp_f729y5_postmeta
		WHERE meta_key = "_tribe_rsvp_email") as email_t
		on name_t.post_id = email_t.post_id 
	LEFT JOIN (SELECT post_id, CAST(meta_value AS UNSIGNED) AS event_id FROM wp_f729y5_postmeta
		WHERE meta_key = "_tribe_rsvp_event") as event_lookup_t
		on name_t.post_id = event_lookup_t.post_id 
	LEFT JOIN (SELECT ID, post_date as ticket_time FROM wp_f729y5_posts) as event_time
		on name_t.post_id = event_time.ID 
	-- not in use, but helpful to get custom field values
	LEFT JOIN (SELECT post_id, meta_value AS airtable_id 
		FROM wp_f729y5_postmeta 
		WHERE meta_key = "_ecp_custom_41" AND meta_value NOT IN ("","None")) AS meta_airtable
		on meta_airtable.post_id = event_lookup_t.event_id 
	LEFT JOIN (SELECT post_id, meta_value AS zoom_link
		FROM wp_f729y5_postmeta 
		WHERE meta_key = "_tribe_events_zoom_join_url") AS zoom_t
		on zoom_t.post_id = event_lookup_t.event_id 
	LEFT JOIN (SELECT post_id, meta_value AS other_link 
		FROM wp_f729y5_postmeta 
		WHERE meta_key = "_tribe_events_virtual_url") AS other_t
		on other_t.post_id = event_lookup_t.event_id 	
	LEFT JOIN (SELECT ID, post_title as eventName, post_name as eventURL from wp_f729y5_posts) as posts
		on posts.ID = event_lookup_t.event_id 
	LEFT JOIN (SELECT post_id, meta_value AS eventDt FROM wp_f729y5_postmeta
		WHERE meta_key = "_EventStartDate") as event_start
	 	on posts.ID = event_start.post_id 
	-- get venue info
	LEFT JOIN (SELECT post_id, meta_value AS venueId FROM wp_f729y5_postmeta
		WHERE meta_key = "_EventVenueID") as venue
	 	on posts.ID = venue.post_id
	LEFT JOIN (SELECT post_id, meta_value AS eventLocation FROM wp_f729y5_postmeta
		WHERE meta_key = "_VenueAddress") as event_loc
	 	on venue.venueId = event_loc.post_id
	-- ticket info
	LEFT JOIN (SELECT post_id, meta_value AS survey FROM wp_f729y5_postmeta
		WHERE meta_key = "_tribe_tickets_meta") as survey_t
		on name_t.post_id = survey_t.post_id 
	LEFT JOIN (SELECT post_id, 
		CAST(meta_value AS UNSIGNED) as product_id FROM wp_f729y5_postmeta
		WHERE meta_key = '_tribe_rsvp_product' ) as rsvp_link
		on rsvp_link.post_id  = name_t.post_id
	LEFT JOIN (SELECT ID, post_title as ticket_name from wp_f729y5_posts 
		WHERE post_type = 'tribe_rsvp_tickets') as product_name
		on rsvp_link.product_id = product_name.ID
