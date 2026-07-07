"""
ATS-Friendly Resume Templates for different styles and industries.
Templates are designed to pass ATS parsing while maintaining visual hierarchy.
"""

TEMPLATES = {
    "minimalist": {
        "id": "minimalist",
        "name": "Minimalist (ATS Optimized)",
        "description": "Clean, simple format. Perfect for ATS systems. Best for: All roles",
        "difficulty": "easy",
        "example": """JOHN SMITH
john@email.com | +1-555-0123 | linkedin.com/in/johnsmith | GitHub: github.com/johnsmith

PROFESSIONAL SUMMARY
Results-driven Software Engineer with 5+ years of experience building scalable systems using Python, AWS, and React. Proven track record of improving performance by 40% and leading cross-functional teams of 8+.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL, Bash
Frontend: React, Next.js, HTML, CSS, Tailwind CSS
Backend: FastAPI, Django, Node.js, Express, PostgreSQL
Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, Terraform, GitHub Actions
Tools: Git, JIRA, Confluence, Postman, VS Code

PROFESSIONAL EXPERIENCE

Senior Software Engineer | TechCorp Inc. | Jan 2022 - Present
- Led architecture redesign of microservices, reducing latency by 40% and cutting infrastructure costs by $200K annually
- Mentored team of 5 junior engineers, conducting weekly code reviews and technical training sessions
- Implemented CI/CD pipeline using GitHub Actions, reducing deployment time from 2 hours to 15 minutes
- Designed real-time analytics dashboard processing 10M+ events daily using Apache Kafka and PostgreSQL

Software Engineer | DataFlow Systems | Jun 2020 - Dec 2021
- Built and maintained REST APIs serving 5M+ requests daily with 99.9% uptime
- Optimized database queries, improving query performance by 55% and reducing server load by 30%
- Implemented automated testing suite with 85% code coverage, reducing production bugs by 60%
- Collaborated with product team to deliver 12+ features on time and within budget

Junior Developer | WebStart Ltd. | Aug 2018 - May 2020
- Developed responsive web applications using React and TypeScript, serving 100K+ monthly users
- Fixed 200+ bugs and improved application performance across 8 production systems
- Contributed to open-source projects with 50+ merged pull requests
- Participated in agile ceremonies and code reviews, enhancing team velocity by 25%

PROJECTS

Portfolio Website | React, Next.js, Tailwind CSS, Vercel | github.com/johnsmith/portfolio
- Built personal portfolio generating 2K+ visitor inquiries monthly
- Implemented SEO optimization, improving Google search ranking from 50+ to top 5 for target keywords
- Achieved 95+ Lighthouse score with optimized images, fonts, and code splitting

Real-time Chat Application | Node.js, Socket.io, MongoDB, Docker | github.com/johnsmith/chat-app
- Engineered real-time messaging system supporting 500+ concurrent users
- Implemented Redis caching, reducing database queries by 70% and improving response times to <100ms
- Deployed on AWS ECS, supporting auto-scaling for 10x traffic spikes

EDUCATION

Bachelor of Science in Computer Science | State University | May 2018
GPA: 3.8/4.0 | Dean's List all semesters

CERTIFICATIONS & ACHIEVEMENTS
- AWS Certified Solutions Architect Associate (2021)
- Google Cloud Certified Associate Cloud Engineer (2022)
- Published 3 technical articles on Medium, reaching 50K+ readers
- Speaker at React Conference 2023 on optimization techniques""",
        "ats_score": 92,
        "pros": ["Highest ATS compatibility", "Clear section headers", "Keyword-rich", "Simple parsing"],
        "cons": ["Basic visual appeal", "Less creative", "Traditional look"],
    },
    
    "skills_first": {
        "id": "skills_first",
        "name": "Skills-First (For Career Changers)",
        "description": "Prioritizes skills over chronology. Best for: Transitions, freelancers, resume gaps",
        "difficulty": "medium",
        "example": """JANE WILLIAMS
jane@email.com | +1-555-9876 | linkedin.com/in/janewilliams

PROFESSIONAL SUMMARY
Full-stack engineer transitioning into DevOps and Cloud Architecture. 3+ years experience with AWS, Kubernetes, and infrastructure-as-code. Seeking to leverage automation skills in high-growth startup environment.

CORE COMPETENCIES
Cloud & Infrastructure: AWS (EC2, RDS, S3, CloudFormation, Lambda), Google Cloud Platform, Azure basics
Containerization & Orchestration: Docker, Kubernetes, Helm, Docker Compose
Infrastructure-as-Code: Terraform, Ansible, CloudFormation
CI/CD & Automation: Jenkins, GitHub Actions, GitLab CI, ArgoCD
Monitoring & Logging: Prometheus, Grafana, ELK Stack, DataDog
Programming: Python, Bash, Go, JavaScript
Databases: PostgreSQL, MongoDB, Redis, DynamoDB
Version Control: Git, GitHub, GitLab

PROFESSIONAL EXPERIENCE

Full-Stack Developer → Cloud Engineer | InnovateTech | Aug 2020 - Present
- Architected and deployed microservices on Kubernetes, handling 2M+ daily transactions
- Reduced cloud infrastructure costs by 35% through resource optimization and reserved instances
- Implemented comprehensive monitoring using Prometheus and Grafana, improving incident response time by 50%
- Automated deployment pipeline using Terraform and GitHub Actions, enabling 50+ deployments daily

Web Developer | StartupHub | Jan 2019 - Jul 2020
- Containerized legacy monolith into 12 microservices using Docker, improving deployment speed by 10x
- Managed AWS infrastructure supporting 100K+ concurrent users
- Implemented automated scaling policies, reducing costs by 25% during off-peak hours
- Led migration from on-premise to AWS cloud, handling 2TB+ data transfer with zero downtime

Junior Developer | TechStudio | Jun 2018 - Dec 2018
- Built responsive web applications using React and Node.js
- Assisted with AWS infrastructure setup and Docker containerization
- Learned and applied CI/CD best practices in fast-paced environment

PROJECTS & ACHIEVEMENTS

Kubernetes Migration Project | Saved $150K annually
- Migrated 8 applications from Docker Swarm to Kubernetes with zero production downtime
- Automated cluster scaling and resource management using custom Python operators
- Reduced infrastructure complexity and improved team productivity

Cloud Cost Optimization | Achieved 40% cost reduction
- Analyzed spending patterns and identified wasteful resources
- Implemented cost allocation tags and automated cleanup processes
- Migrated batch jobs to spot instances and reserved instances

CERTIFICATIONS
- AWS Certified Solutions Architect Associate (2022)
- Kubernetes Application Developer - CKAD (2023)
- HashiCorp Certified: Terraform Associate (2022)

EDUCATION
Bachelor of Science in Information Technology | Tech University | May 2018""",
        "ats_score": 88,
        "pros": ["Great for career changes", "Emphasizes relevant skills", "Flexible format", "Good for freelancers"],
        "cons": ["May confuse chronological sorting", "Requires context explanation"],
    },
    
    "chronological": {
        "id": "chronological",
        "name": "Chronological (Traditional)",
        "description": "Time-based experience focus. Best for: Linear career paths, senior roles",
        "difficulty": "easy",
        "example": """MICHAEL JOHNSON
michael@email.com | +1-555-5555 | linkedin.com/in/michaeljohnson | Portfolio: johnsondev.com

OBJECTIVE
Experienced Software Engineering Manager seeking Director-level position to lead high-performing teams and drive technical innovation at scale.

PROFESSIONAL EXPERIENCE

Vice President of Engineering | TechGiant Inc. | Mar 2023 - Present
- Lead team of 25 engineers across 3 locations managing $5M+ annual budget
- Increased team velocity by 45% through improved processes, tooling, and mentorship
- Reduced time-to-market for new features from 3 months to 6 weeks through agile transformation
- Established engineering culture focused on quality, mentoring 15+ engineers promoted to senior roles

Senior Engineering Manager | CloudSys | Jan 2021 - Feb 2023
- Managed 12 engineers across Backend and DevOps teams with $1.2M budget
- Improved code quality metrics: increased test coverage from 45% to 82% and reduced production incidents by 60%
- Led successful migration of 10 microservices to Kubernetes, reducing operational overhead by 30%
- Championed diversity hiring, growing women in engineering from 10% to 28%

Senior Software Engineer | DataStream | Jun 2018 - Dec 2020
- Architected microservices platform processing 100M+ events daily
- Led 4-person team building real-time analytics engine, generating $500K revenue
- Designed distributed caching layer using Redis, improving response times by 70%
- Mentored 3 junior engineers, all promoted to mid-level roles

Software Engineer | WebFirst | Mar 2016 - May 2018
- Developed full-stack web applications using Python, React, and PostgreSQL
- Optimized critical queries reducing database load by 50%
- Implemented automated testing framework improving code quality and deployment confidence
- Collaborated with product team to ship 20+ features quarterly

Junior Software Engineer | StartupXYZ | Jul 2015 - Feb 2016
- Built RESTful APIs and web interfaces for growing SaaS platform
- Participated in code reviews and learned best practices from senior team
- Fixed 100+ bugs and improved system reliability

EDUCATION

Master of Science in Computer Science | Stanford University | May 2015
GPA: 3.7/4.0 | Focus: Distributed Systems

Bachelor of Science in Computer Science | UC Berkeley | May 2013
GPA: 3.8/4.0 | Honors: Graduated with Distinction

CERTIFICATIONS
- AWS Certified Solutions Architect Professional (2022)
- PMP (Project Management Professional) (2021)
- Six Sigma Green Belt (2020)

TECHNICAL SKILLS
Languages: Python, Java, JavaScript, Scala
Backend: FastAPI, Django, Spring Boot, Node.js
Databases: PostgreSQL, MongoDB, DynamoDB, Elasticsearch
Cloud: AWS, GCP, Kubernetes, Docker
Tools: Git, JIRA, Terraform, Jenkins""",
        "ats_score": 90,
        "pros": ["Clear progression", "Easy for ATS", "Great for senior roles", "Traditional format"],
        "cons": ["May highlight employment gaps", "Not ideal for career changers"],
    },
    
    "hybrid": {
        "id": "hybrid",
        "name": "Hybrid (Skills + Experience)",
        "description": "Best of both worlds. Combines skills visibility with chronological work history.",
        "difficulty": "medium",
        "example": """SARAH RODRIGUEZ
sarah@email.com | +1-555-0987 | linkedin.com/in/sarahrodriguez | GitHub: github.com/sarahrodriguez

PROFESSIONAL SUMMARY
Full-Stack Engineering Manager with 8+ years building scalable platforms. Expert in Python, React, AWS, and leading remote teams. Proven track record: 3x headcount growth, 50% cost reduction, 4 direct reports promoted to management.

KEY SKILLS & EXPERTISE
Technical Leadership: Software architecture, tech strategy, system design, code reviews, technical mentoring
Backend Development: Python, FastAPI, Django, PostgreSQL, MongoDB, Redis, Microservices
Frontend Development: React, Next.js, TypeScript, Tailwind CSS, Jest, Storybook
Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD, Infrastructure-as-Code
Management: Team building, performance management, cross-functional collaboration, agile methodologies
Specialties: Scaling systems to 100M+ users, cost optimization, mentorship

PROFESSIONAL EXPERIENCE

Senior Manager, Engineering | TechPlatform Inc. | Jan 2022 - Present
Leadership & Impact
- Built and scaled engineering team from 3 to 8 people, promoting 2 engineers to senior roles
- Reduced cloud infrastructure costs by $300K annually through optimization initiatives
- Improved team productivity by 40% through process improvements and better tooling

Technical Contributions
- Redesigned core API architecture for 10x throughput improvement
- Led migration to microservices, reducing deployment time from 4 hours to 15 minutes
- Established quality standards: increased test coverage to 85% and reduced production incidents by 70%

Lead Software Engineer | DataCore Systems | Jun 2019 - Dec 2021
Technical Achievements
- Architected distributed system handling 50M+ daily transactions with 99.95% uptime
- Optimized critical queries reducing database load by 60% and API response time from 800ms to 150ms
- Built automated monitoring system using Prometheus/Grafana reducing MTTR by 50%

Team & Leadership
- Mentored team of 4 engineers through code reviews and technical guidance
- Established best practices in code quality, testing, and documentation
- Led technical interviews and contributed to hiring process for 6 senior engineers

Software Engineer II | StartupVenture | Feb 2018 - May 2019
- Developed full-stack features used by 200K+ users daily
- Implemented Redis caching layer reducing database queries by 70%
- Built automated testing suite with 80% code coverage
- Collaborated with product team to deliver features on tight deadlines

Software Engineer | WebConnect | Aug 2016 - Jan 2018
- Built responsive web applications using React and Node.js
- Contributed to backend API development serving 50K+ daily active users
- Implemented performance optimizations improving page load time by 40%
- Participated in code reviews and learned from senior engineers

EDUCATION

Bachelor of Science in Software Engineering | Tech Institute | May 2016
GPA: 3.7/4.0 | Relevant Coursework: Distributed Systems, Database Design, Software Architecture

CERTIFICATIONS & RECOGNITIONS
- AWS Certified Solutions Architect Associate (2021)
- Google Cloud Certified Associate Cloud Engineer (2022)
- Speaker: "Scaling Engineering Teams" - Tech Conference 2023

NOTABLE ACHIEVEMENTS
- Led successful product launch generating $2M revenue in first year
- Reduced time-to-market for new features by 60% through process optimization
- Increased team satisfaction score from 6.5 to 8.5 out of 10 through culture initiatives""",
        "ats_score": 94,
        "pros": ["Best ATS score", "Shows skills clearly", "Maintains chronology", "Flexible"],
        "cons": ["Requires careful formatting", "Can be longer"],
    },
}

# Industry-specific role suggestions
INDUSTRY_ROLES = {
    "software_engineer": [
        "Backend Engineer",
        "Frontend Engineer", 
        "Full-Stack Engineer",
        "DevOps Engineer",
        "Machine Learning Engineer",
        "Site Reliability Engineer (SRE)",
        "Solutions Engineer",
        "Staff/Principal Engineer",
    ],
    "data_science": [
        "Data Scientist",
        "Data Engineer",
        "Analytics Engineer",
        "Machine Learning Engineer",
        "ML Operations (MLOps) Engineer",
        "Research Scientist",
        "BI/Analytics Developer",
        "Data Analyst",
    ],
    "product": [
        "Product Manager",
        "Senior Product Manager",
        "Associate Product Manager",
        "Product Operations Manager",
        "Product Marketing Manager",
        "Growth Product Manager",
        "Technical Product Manager",
    ],
    "management": [
        "Engineering Manager",
        "Senior Engineering Manager",
        "Director of Engineering",
        "VP of Engineering",
        "Technical Lead Manager",
        "Team Lead",
        "Scrum Master / Agile Coach",
    ],
    "design": [
        "Product Designer",
        "UX Designer",
        "UI Designer",
        "Design Lead",
        "Design Manager",
        "User Research",
        "Design Systems Lead",
    ],
}
