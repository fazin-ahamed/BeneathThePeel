extends RefCounted


static func dialogue(key: String) -> Array:
	match key:
		"intro":
			return [
				{
					"speaker": "The Narrator",
					"text": "The temple had been abandoned for years.",
					"portrait": "narrator"
				},
				{
					"speaker": "The Narrator",
					"text": "At least, that is what everyone believed.",
					"portrait": "narrator"
				}
			]
		"enter_temple":
			return [
				{
					"speaker": "You",
					"text": "Why is this place completely empty?",
					"portrait": "player"
				},
				{
					"speaker": "The Narrator",
					"text":
					"Somewhere beneath the stone floor, something answered with a slow, heavy thump.",
					"portrait": "narrator"
				}
			]
		"leave_before_prayer":
			return [
				{
					"speaker": "You",
					"text":
					"I came all this way to pray. Leaving now would be suspiciously sensible.",
					"portrait": "player"
				}
			]
		"prayer":
			return [
				{
					"speaker": "You",
					"text": "Please grant me a calm evening and a safe journey home.",
					"portrait": "player"
				},
				{"speaker": "The Narrator", "text": "THUMP.", "portrait": "narrator"},
				{
					"speaker": "You",
					"text": "...and perhaps quieter plumbing.",
					"portrait": "player"
				},
				{
					"speaker": "The Narrator",
					"text":
					"The candles bent toward the floor. A curved symbol briefly glowed beneath the altar.",
					"portrait": "narrator"
				}
			]
		"manhole":
			return [
				{
					"speaker": "The Narrator",
					"text":
					"Some warnings are written on signs. Others knock from beneath your feet.",
					"portrait": "narrator"
				},
				{"speaker": "You", "text": "That is an unusually round pudd—", "portrait": "player"}
			]
		"wakeup":
			return [
				{
					"speaker": "The Narrator",
					"text":
					(
						"Cold water carried him through darkness until the current finally abandoned "
						+ "him on a stone ledge."
					),
					"portrait": "narrator"
				},
				{"speaker": "You", "text": "My shoe is gone.", "portrait": "player"},
				{
					"speaker": "You",
					"text": "My sock is on the ceiling. I have several questions.",
					"portrait": "player"
				},
				{
					"speaker": "The Narrator",
					"text": "The same ritual thumping echoed from deeper underground.",
					"portrait": "narrator"
				}
			]
		"stairs_before_window":
			return [
				{
					"speaker": "You",
					"text":
					"Going deeper without checking that window would be irresponsible. Even by today's standards.",
					"portrait": "player"
				}
			]
		"cult_window":
			return [
				{"speaker": "Cult", "text": "THE PEEL PROTECTS.", "portrait": "cultist"},
				{"speaker": "Cult", "text": "THE FLESH PROVIDES.", "portrait": "cultist"},
				{"speaker": "Cult", "text": "THE POTASSIUM ASCENDS.", "portrait": "cultist"},
				{"speaker": "You", "text": "They sound terrifying.", "portrait": "player"},
				{"speaker": "You", "text": "And medically well informed.", "portrait": "player"},
				{
					"speaker": "The Narrator",
					"text": "A staircase beside the window descended toward the ceremony.",
					"portrait": "narrator"
				}
			]
		"induction":
			return [
				{
					"speaker": "Guard",
					"text": "State your sacred purpose.",
					"portrait": "guard",
					"choices":
					[
						{"text": "I am the plumber.", "value": "plumber"},
						{"text": "I fell through a hole.", "value": "hole"},
						{"text": "Nice robes.", "value": "robes"}
					]
				},
				{
					"speaker": "Guard",
					"text":
					"Correct. The new initiate was expected to be confused, damp and poorly briefed.",
					"portrait": "guard"
				},
				{
					"speaker": "Guard",
					"text": "From this moment onward, you are Brother Potassium.",
					"portrait": "guard"
				},
				{"speaker": "You", "text": "Do I get a choice?", "portrait": "player"},
				{"speaker": "Guard", "text": "You already chose 'nice robes.'", "portrait": "guard"}
			]
		"hq_intro":
			return [
				{
					"speaker": "The Curator",
					"text": "Brother Potassium. Your lateness has ripened into punctuality.",
					"portrait": "leader"
				},
				{
					"speaker": "You",
					"text": "I do not know what that means.",
					"portrait": "player_robed"
				},
				{
					"speaker": "The Curator",
					"text":
					"Excellent. Report to the Logistics Elder and deliver three Sacred Boxes.",
					"portrait": "leader"
				},
				{
					"speaker": "The Curator",
					"text": "Do not open them. Do not shake them. Do not listen when they whisper.",
					"portrait": "leader"
				},
				{"speaker": "Box, somewhere", "text": "ripe...", "portrait": ""}
			]
		"foreman_start":
			return [
				{
					"speaker": "Logistics Elder",
					"text": "Three boxes. Three marked destinations. Zero workplace incidents.",
					"portrait": "cultist"
				},
				{
					"speaker": "Logistics Elder",
					"text":
					"Our previous record is negative four incidents, so expectations are flexible.",
					"portrait": "cultist"
				}
			]
		"foreman_boxes_progress":
			return [
				{
					"speaker": "Logistics Elder",
					"text":
					"The Sacred Boxes remain tragically undelivered. Storage is through the northern door.",
					"portrait": "cultist"
				}
			]
		"foreman_after_boxes":
			return [
				{
					"speaker": "Logistics Elder",
					"text":
					"The boxes are placed. Now prove your devotion and earn three security seals.",
					"portrait": "cultist"
				},
				{
					"speaker": "Logistics Elder",
					"text":
					"Polish The Curved One. Feed the Ripening Engine. Locate Brother Cavendish.",
					"portrait": "cultist"
				}
			]
		"foreman_done":
			return [
				{
					"speaker": "Logistics Elder",
					"text":
					(
						"Three seals? Impressive. You are now authorised to leave, which naturally "
						+ "means you are forbidden to leave."
					),
					"portrait": "cultist"
				}
			]
		"box_pickup":
			return [
				{"speaker": "Box", "text": "ripe...", "portrait": ""},
				{
					"speaker": "You",
					"text": "I am going to pretend that was the floor.",
					"portrait": "player_robed"
				}
			]
		"already_carrying":
			return [
				{
					"speaker": "You",
					"text": "One whispering box at a time is enough.",
					"portrait": "player_robed"
				}
			]
		"wrong_delivery":
			return [
				{
					"speaker": "You",
					"text":
					"The symbol on this box points somewhere else. Even evil logistics has standards.",
					"portrait": "player_robed"
				}
			]
		"boxes_complete":
			return [
				{
					"speaker": "Logistics Elder",
					"text": "Perfect. None of them exploded.",
					"portrait": "cultist"
				},
				{"speaker": "Box", "text": "yet...", "portrait": ""},
				{
					"speaker": "Logistics Elder",
					"text": "Ignore that. Begin the three sacred duties.",
					"portrait": "cultist"
				}
			]
		"duties_locked":
			return [
				{
					"speaker": "Cultist",
					"text":
					"Only certified box handlers may perform sacred duties. Deliver all three boxes first.",
					"portrait": "cultist"
				}
			]
		"statue":
			return [
				{
					"speaker": "Cultist",
					"text": "Polish the sacred object. Do not call it a banana.",
					"portrait": "cultist"
				},
				{
					"speaker": "You",
					"text": "It is very clearly a banana.",
					"portrait": "player_robed"
				},
				{"speaker": "Cultist", "text": "It is The Curved One.", "portrait": "cultist"},
				{"speaker": "You", "text": "A curved what?", "portrait": "player_robed"},
				{"speaker": "Cultist", "text": "One.", "portrait": "cultist"}
			]
		"statue_done":
			return [
				{
					"speaker": "You",
					"text": "It is already polished enough to reflect my poor decisions.",
					"portrait": "player_robed"
				}
			]
		"fuel_left":
			return [
				{
					"speaker": "Cultist",
					"text": "Premium yellow fuel. Naturally curved. Locally sourced.",
					"portrait": "cultist"
				}
			]
		"fuel_right":
			return [
				{"speaker": "You", "text": "This one is moving.", "portrait": "player_robed"},
				{"speaker": "Cultist", "text": "Freshness.", "portrait": "cultist"}
			]
		"fuel_apple":
			return [
				{
					"speaker": "You",
					"text": "What happens if I feed it an apple?",
					"portrait": "player_robed"
				},
				{
					"speaker": "Cultist",
					"text": "The machine rejects doctrinal inconsistency.",
					"portrait": "cultist"
				}
			]
		"vending_machine":
			return [
				{
					"speaker": "Vending Machine",
					"text": "PAYMENT ACCEPTED: ONE PEEL. PRODUCT DISPENSED: ONE MORE BANANA.",
					"portrait": ""
				},
				{
					"speaker": "You",
					"text": "This economy is structurally unsound.",
					"portrait": "player_robed"
				}
			]
		"cult_noticeboard":
			return [
				{
					"speaker": "Noticeboard",
					"text":
					"REMINDERS: Iron robes before ceremony. Report all apples. Dental claims close Friday.",
					"portrait": ""
				},
				{
					"speaker": "Noticeboard",
					"text":
					"THURSDAY SEMINAR: Why Potassium Has One Electron It Desperately Wants To Give Away.",
					"portrait": ""
				}
			]
		"ritual_drum":
			return [
				{
					"speaker": "The Narrator",
					"text":
					"The dreadful underground thumping came from a ceremonial drum labelled DO NOT OVER-RIPEN.",
					"portrait": "narrator"
				},
				{
					"speaker": "You",
					"text": "I crossed a sewer for percussion maintenance.",
					"portrait": "player_robed"
				}
			]
		"sewer_sign":
			return [
				{
					"speaker": "Corroded Sign",
					"text": "LOWER TEMPLE — SANITATION ACCESS — ABSOLUTELY NO APPLES.",
					"portrait": ""
				},
				{
					"speaker": "You",
					"text": "The apple rule has infrastructure support.",
					"portrait": "player"
				}
			]
		"potassium_configuration":
			return [
				{"speaker": "Compliance Panel", "text": "K — ATOMIC NUMBER 19", "portrait": ""},
				{
					"speaker": "Compliance Panel",
					"text": "ELECTRONS BY SHELL: 2, 8, 8, 1",
					"portrait": ""
				},
				{
					"speaker": "Compliance Panel",
					"text": "ELECTRON CONFIGURATION: [Ar] 4s¹",
					"portrait": ""
				},
				{
					"speaker": "You",
					"text":
					"One electron in the outermost shell. Even the chemistry is trying to escape.",
					"portrait": "player_robed"
				},
				{"speaker": "Cultist", "text": "We call it sacred valence.", "portrait": "cultist"}
			]
		"engine_not_ready":
			return [
				{
					"speaker": "Machine",
					"text": "INSUFFICIENT RIPENESS. INSERT THREE UNITS OF FRUIT-ADJACENT FUEL.",
					"portrait": ""
				}
			]
		"engine_complete":
			return [
				{"speaker": "Machine", "text": "POTASSIUM PRESSURE: UNREASONABLE.", "portrait": ""},
				{
					"speaker": "Cultist",
					"text": "Beautiful. It has not screamed like that in weeks.",
					"portrait": "cultist"
				}
			]
		"engine_done":
			return [
				{
					"speaker": "Machine",
					"text": "PLEASE DO NOT FEED THE ENGINE AGAIN.",
					"portrait": ""
				}
			]
		"locker_1":
			return [
				{
					"speaker": "You",
					"text": "Forty-seven identical left sandals.",
					"portrait": "player_robed"
				},
				{
					"speaker": "You",
					"text": "Somewhere, forty-seven people are having a worse day.",
					"portrait": "player_robed"
				}
			]
		"locker_2":
			return [
				{
					"speaker": "Note",
					"text": "REMEMBER: Casual Friday still requires ceremonial hoods.",
					"portrait": ""
				}
			]
		"locker_3":
			return [
				{
					"speaker": "You",
					"text": "A dental insurance brochure. Surprisingly comprehensive.",
					"portrait": "player_robed"
				}
			]
		"locker_5":
			return [
				{"speaker": "Locker", "text": "hissssss...", "portrait": ""},
				{
					"speaker": "You",
					"text": "That one can remain closed.",
					"portrait": "player_robed"
				}
			]
		"cavendish":
			return [
				{
					"speaker": "Brother Cavendish",
					"text": "Quiet! I discovered the Great Ripening plan.",
					"portrait": "cavendish"
				},
				{
					"speaker": "Brother Cavendish",
					"text":
					"Thousands of boxes will be sent across the world. At midnight, every one of them opens.",
					"portrait": "cavendish"
				},
				{"speaker": "You", "text": "Then come with me.", "portrait": "player_robed"},
				{
					"speaker": "Brother Cavendish",
					"text": "I cannot. They have dental insurance.",
					"portrait": "cavendish"
				},
				{
					"speaker": "Brother Cavendish",
					"text":
					"Take my security seal. Save yourself before the fruit becomes geopolitical.",
					"portrait": "cavendish"
				}
			]
		"locker_empty":
			return [
				{
					"speaker": "You",
					"text": "Already searched. Still disappointingly empty.",
					"portrait": "player_robed"
				}
			]
		"exit_locked":
			return [
				{
					"speaker": "Door",
					"text": "ACCESS DENIED. THREE SECURITY SEALS REQUIRED.",
					"portrait": ""
				},
				{
					"speaker": "You",
					"text": "A cult with proper access control. Of course.",
					"portrait": "player_robed"
				}
			]
		"escape":
			return [
				{"speaker": "Door", "text": "ACCESS GRANTED. HAVE A RIPE DAY.", "portrait": ""},
				{
					"speaker": "Alarm",
					"text": "UNAUTHORISED DEPARTURE. BROTHER POTASSIUM HAS BECOME A SMOOTHIE.",
					"portrait": ""
				},
				{
					"speaker": "The Curator",
					"text": "SEIZE HIM! AND SOMEBODY WARM UP THE CEREMONIAL SCOOTER!",
					"portrait": "leader"
				}
			]
		"caught":
			return [
				{
					"speaker": "Guard",
					"text": "You have been successfully re-smoothied.",
					"portrait": "guard"
				},
				{"speaker": "You", "text": "That is not a real word.", "portrait": "player_robed"},
				{"speaker": "Guard", "text": "It is in the handbook.", "portrait": "guard"}
			]
		"ending_surface":
			return [
				{
					"speaker": "The Narrator",
					"text":
					(
						"Morning arrived with the confidence of a day that knew nothing about the "
						+ "underground fruit cult."
					),
					"portrait": "narrator"
				},
				{
					"speaker": "You",
					"text": "I escaped. I am never entering a mysterious building again.",
					"portrait": "player_robed"
				},
				{
					"speaker": "The Narrator",
					"text": "A wooden box landed beside him.",
					"portrait": "narrator"
				},
				{"speaker": "Box", "text": "ripe.", "portrait": ""}
			]
		"ending_apocalypse":
			return [
				{
					"speaker": "News Broadcast",
					"text":
					"Authorities advise citizens not to panic and not to consume the unexplained fruit.",
					"portrait": ""
				},
				{
					"speaker": "The Curator",
					"text": "THE GREAT RIPENING HAS BEGUN!",
					"portrait": "leader"
				}
			]
		"ending_final":
			return [
				{"speaker": "You", "text": "I should have taken the stairs.", "portrait": "banana"}
			]
		_:
			return []
