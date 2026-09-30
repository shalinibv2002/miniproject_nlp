"""GROUND-TRUTH TRAINING CORPUS for the classifier (Phase 5).

This is SEPARATE from real institutional_activities data. These sample
texts describe typical institutional activity types and are used ONLY to
train and evaluate the four models. They are never written to the
institutional_activities table.
"""

# (text, [category code(s)]) -- multi-label
LABELED_SAMPLES = [
    # Workshop
    ("Hands-on workshop on Python programming for second year students conducted in the computer lab.", ["WORKSHOP"]),
    ("A two day workshop on IoT using Arduino with practical sessions and kits given to all participants.", ["WORKSHOP"]),
    ("Three day hands-on workshop on additive manufacturing and 3D printing for mechanical students.", ["WORKSHOP"]),
    # Seminar
    ("Technical seminar on latest developments in renewable energy systems by an industry expert.", ["SEMINAR"]),
    ("Department seminar on machine learning applications in civil engineering materials.", ["SEMINAR"]),
    # Conference
    ("International conference on smart computing and communication organized with paper presentations from 12 countries.", ["CONFERENCE"]),
    ("National conference on emerging trends in electrical engineering with invited keynote speakers.", ["CONFERENCE"]),
    # Symposium
    ("Annual technical symposium of the computer science association with paper and project displays.", ["SYMPOSIUM"]),
    ("Student symposium on recent advances in automobile engineering with student paper contest.", ["SYMPOSIUM"]),
    # Guest Lecture
    ("Guest lecture on entrepreneurship skills by a successful startup founder for MBA students.", ["GUEST_LECTURE"]),
    ("Invited lecture on VLSI design by an alumnus working at a leading semiconductor company.", ["GUEST_LECTURE"]),
    # FDP
    ("Faculty development programme on outcome based education and NBA accreditation for all faculty.", ["FDP"]),
    ("One week FDP on artificial intelligence in higher education offered to teaching staff of the institute.", ["FDP"]),
    # STTP
    ("Short term training programme on cyber security for faculty and research scholars.", ["STTP"]),
    ("Two week STTP on deep learning and computer vision funded by the central government agency.", ["STTP"]),
    # Hackathon
    ("24 hour hackathon on smart solutions for agriculture with prizes for the top three teams.", ["HACKATHON"]),
    ("National level hackathon on fintech conducted in partnership with a leading bank.", ["HACKATHON"]),
    # Tech Fest
    ("Annual technical festival with robo wars, project expo and coding competitions across the campus.", ["TECH_FEST"]),
    ("Techno-culturals fest celebrating innovation with workshops and tech exhibits.", ["TECH_FEST"]),
    # Cultural Event
    ("Cultural evening with dance and music performances by students as part of the annual day.", ["CULTURAL"]),
    ("Inter-department cultural competition with singing, dance and drama events.", ["CULTURAL"]),
    # Sports
    ("Inter-collegiate cricket tournament held on the college ground over ten days.", ["SPORTS"]),
    ("Annual sports day with track and field events, followed by prize distribution ceremony.", ["SPORTS"]),
    ("State level volleyball tournament hosted by the college sports department.", ["SPORTS"]),
    # NCC
    ("NCC cadets participated in the annual training camp and demonstrated drill and firing skills.", ["NCC"]),
    ("NCC special camp on environmental awareness conducted in the adopted village.", ["NCC"]),
    # NSS
    ("NSS unit organized a blood donation camp in association with the district blood bank.", ["NSS"]),
    ("National service scheme volunteers carried out a cleanliness drive and tree plantation in the campus.", ["NSS"]),
    # Clubs and Chapters
    ("IEEE student chapter organized a session on careers in engineering for final year students.", ["CLUB"]),
    ("Technical association meeting of the mechanical department with student paper presentations.", ["CLUB"]),
    ("Coding club conducted competitive programming practice sessions every weekend.", ["CLUB"]),
    # Outreach
    ("Outreach programme for rural school students on basics of computer science with free course.", ["OUTREACH"]),
    ("Faculty visited nearby schools to conduct science demonstration sessions for school children.", ["OUTREACH"]),
    # Industry Collaboration
    ("Memorandum of understanding signed with a leading software company for internships and training.", ["INDUSTRY"]),
    ("Industry visit to an automobile manufacturing plant for final year mechanical students.", ["INDUSTRY"]),
    ("Industry collaboration for setting up a center of excellence in data analytics.", ["INDUSTRY"]),
    # Achievement and Award
    ("Student team won the national level project award for their assistive device design.", ["ACHIEVEMENT"]),
    ("Faculty member received the best researcher award for outstanding publications during the year.", ["ACHIEVEMENT"]),
    ("College was ranked among top engineering institutions in the national survey.", ["ACHIEVEMENT"]),
    # Placement
    ("Placement drive conducted by a global software company with aptitude and technical rounds.", ["PLACEMENT"]),
    ("Career guidance session on resume writing and interview skills for pre-final year students.", ["PLACEMENT"]),
    ("Training on aptitude and soft skills organized by the placement cell for all final year students.", ["PLACEMENT"]),
    # Internship
    ("Industrial training internship for civil engineering students at a construction firm.", ["INTERNSHIP"]),
    ("Summer internship programme in embedded systems with a leading electronics company.", ["INTERNSHIP"]),
    # Research
    ("Sponsored research project sanctioned by the department of science and technology on water quality.", ["RESEARCH"]),
    ("Research paper presented at an international journal was selected for the best paper award.", ["RESEARCH"]),
    ("Consultancy work carried out for a local industry on quality testing of materials.", ["RESEARCH"]),
    # Alumni
    ("Alumni meet organized for the silver jubilee batch of 2000 with reminiscence and felicitation.", ["ALUMNI"]),
    ("Alumni networking dinner held to encourage alumni contributions to the institution.", ["ALUMNI"]),
    # Orientation
    ("Induction and orientation programme conducted for the first year students and their parents.", ["ORIENTATION"]),
    ("Annual convocation ceremony where degrees were awarded to the graduating batch.", ["ORIENTATION"]),
    # Campus Life
    ("Hostel festival with games and cultural events organized for resident students.", ["CAMPUS"]),
    ("Health check-up camp organized for students and staff on the campus premises.", ["CAMPUS"]),
    # Webinar
    ("Webinar on cloud computing fundamentals open to students across the country.", ["WEBINAR"]),
    ("Online talk series on data science careers for third year students via video conference.", ["WEBINAR"]),
    ("Virtual international webinar on green building practices attended by faculty worldwide.", ["WEBINAR"]),
]

# A few multi-label examples
LABELED_SAMPLES += [
    ("National conference on artificial intelligence and a hands-on workshop on machine learning were held over two days.", ["CONFERENCE", "WORKSHOP"]),
    ("FDP on advanced teaching methods followed by a webinar on online evaluation tools.", ["FDP", "WEBINAR"]),
    ("Sports day celebrations included cultural performances by student teams in the evening.", ["SPORTS", "CULTURAL"]),
    ("Industry collaboration workshop on VLSI design tools for students and faculty.", ["INDUSTRY", "WORKSHOP"]),
    ("NSS volunteers and NCC cadets jointly organized a blood donation camp in the campus.", ["NSS", "NCC"]),
]

# Additional multi-variant samples to build a corpus large enough for
# multi-label model training (~150 samples). All still synthetic training
# text with explicitly labeled categories.
LABELED_SAMPLES += [
    # Workshop
    ("Practical workshop on excel and data analysis for staff and students was conducted in the computer centre.", ["WORKSHOP"]),
    ("Workshop on effective communication skills with role play sessions for students.", ["WORKSHOP"]),
    ("Two-day hands-on workshop on drone building and remote sensing for ECE students.", ["WORKSHOP"]),
    # Seminar
    ("Departmental seminar on structural health monitoring of bridges presented by research scholars.", ["SEMINAR"]),
    ("Seminar on intellectual property rights and patent filing for faculty members.", ["SEMINAR"]),
    # Conference
    ("International conference on renewable energy attracted delegates from six countries with paper tracks.", ["CONFERENCE"]),
    ("National conference on cyber security with industry paper presentations near Chennai.", ["CONFERENCE"]),
    # Symposium
    ("Annual symposium of the electrical association with project exhibition and contests.", ["SYMPOSIUM"]),
    ("Symposium cum workshop on emerging VLSI tools organized by research centre.", ["SYMPOSIUM"]),
    # Guest Lecture
    ("Guest lecture on financial literacy and investment basics for commerce students.", ["GUEST_LECTURE"]),
    ("Guest lecture by an ISRO scientist on satellite technology for aeronautical enthusiasts.", ["GUEST_LECTURE"]),
    # FDP
    ("Online faculty development programme on MOODLE and virtual classrooms for teaching staff.", ["FDP", "WEBINAR"]),
    ("Five day FDP on research methodology and publication ethics conducted for young faculty.", ["FDP"]),
    # STTP
    ("Short term training programme on power system protection for engineers from utilities.", ["STTP"]),
    ("STTP on computer aided design tools sponsored by the training department of AICTE.", ["STTP"]),
    # Hackathon
    ("Smart city hackathon for student teams to propose traffic management solutions.", ["HACKATHON"]),
    ("Open source hackathon for building accessibility tools for differently abled persons.", ["HACKATHON"]),
    # Tech Fest
    ("The technical fest featured autonomous vehicle demos and AI challenges over three days.", ["TECH_FEST"]),
    ("Department tech fest with paper presentations, quizzes and software development contest.", ["TECH_FEST"]),
    # Cultural Event
    ("Literary and cultural club celebrated the language day with debates and poetry recitation.", ["CULTURAL"]),
    ("Cultural fest with fashion show, music night and drama performed by students.", ["CULTURAL"]),
    # Sports
    ("Inter-campus basketball league matches were played in the indoor stadium every weekend.", ["SPORTS"]),
    ("Annual athletic meet with 100m sprint, long jump and relay events for all students.", ["SPORTS"]),
    # NCC
    ("NCC cadets took part in the Republic day parade at the district headquarters after regular drill training.", ["NCC"]),
    ("NCC army wing cadets completed the mountaineering basic camp successfully.", ["NCC"]),
    # NSS
    ("NSS special camp for a week in the adopted village with awareness programmes on health and hygiene.", ["NSS"]),
    ("NSS unit conducted free eye camps in rural areas with the support of an eye hospital.", ["NSS"]),
    # Clubs
    ("Robotics club organized inter-school robot battle competition on campus.", ["CLUB"]),
    ("Toastmasters club conducted public speaking workshops for club members.", ["CLUB"]),
    # Outreach
    ("Rural outreach initiative distributed study materials and conducted tuition classes for village children.", ["OUTREACH"]),
    ("Extension lecture series on water conservation organized for local farmers.", ["OUTREACH"]),
    # Industry
    ("MoU signed with an automation company for joint certification programmes in robotics.", ["INDUSTRY"]),
    ("Industry expert panel discussion on the future of electric mobility.", ["INDUSTRY"]),
    # Achievement
    ("Three students received the district-level sports achievement award for their athletic excellence.", ["ACHIEVEMENT", "SPORTS"]),
    ("The innovation lab won the best startup incubator award during the year.", ["ACHIEVEMENT"]),
    # Placement
    ("On campus recruitment drive for software engineering roles was attended by two hundred final year students.", ["PLACEMENT"]),
    ("Placement orientation for parents on the placement process and company profiles.", ["PLACEMENT"]),
    # Internship
    ("Two month manufacturing internship was completed by mechanical students at a steel plant.", ["INTERNSHIP"]),
    ("Data science internship for computer science students with a startup.", ["INTERNSHIP"]),
    # Research
    ("Faculty members filed a design patent for a low cost prosthetic hand.", ["RESEARCH"]),
    ("Sponsored research project on waste water treatment obtained funding from the ministry.", ["RESEARCH"]),
    # Alumni
    ("Alumni association felicitated the outgoing batch with a farewell dinner.", ["ALUMNI"]),
    ("Alumni webinar series on career advice for current students was streamed live.", ["ALUMNI", "WEBINAR"]),
    # Orientation
    ("Welcome and orientation programme for postgraduate students held in the conference hall.", ["ORIENTATION"]),
    ("Convocation day celebrated with the chief guest distributing degrees to graduating students.", ["ORIENTATION"]),
    # Campus
    ("Campus cleanliness drive and beautification programme was organised by the hostel council.", ["CAMPUS"]),
    ("Free vaccination camp arranged on campus for students and their families.", ["CAMPUS"]),
    # Webinar
    ("International webinar on sustainable agriculture practices for agricultural engineering faculty.", ["WEBINAR"]),
    ("Web-based seminar on cracking competitive examinations for placement-bound students.", ["WEBINAR", "PLACEMENT"]),
]


def get_labeled_data():
    return [(text, cats) for text, cats in LABELED_SAMPLES]


def category_codes():
    return sorted({c for _, cats in LABELED_SAMPLES for c in cats})