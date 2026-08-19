import {
  BLOOD_GROUPS,
  type BloodRequest,
  type BloodStock,
  type BloodUnit,
  type Camp,
  type DonationRecord,
  type Notification,
  type SosBroadcast,
  type SosResponse,
  type TestRecord,
  type User,
} from "@/lib/types";

/**
 * MOCK DATA ONLY.
 * Replace these fixtures with Django REST responses; the shapes mirror the
 * expected API payloads so only `src/services/*` needs to change.
 */

export const bloodStock: BloodStock[] = [
  { group: "A+", units: 42, reserved: 6, testing: 5, threshold: 20 },
  { group: "A-", units: 11, reserved: 2, testing: 1, threshold: 12 },
  { group: "B+", units: 36, reserved: 4, testing: 3, threshold: 20 },
  { group: "B-", units: 7, reserved: 1, testing: 2, threshold: 10 },
  { group: "AB+", units: 18, reserved: 3, testing: 1, threshold: 10 },
  { group: "AB-", units: 4, reserved: 0, testing: 1, threshold: 8 },
  { group: "O+", units: 55, reserved: 9, testing: 6, threshold: 25 },
  { group: "O-", units: 9, reserved: 3, testing: 2, threshold: 15 },
];

export const users: User[] = [
  {
    id: "USR-001",
    name: "Dr. Meera Raghavan",
    email: "meera@bms.health",
    role: "SUPER_ADMIN",
    organization: "National Blood Authority",
    status: "ACTIVE",
    joinedAt: "2024-01-12",
  },
  {
    id: "USR-002",
    name: "Arun Prakash",
    email: "arun@citybank.health",
    role: "BLOOD_BANK_ADMIN",
    organization: "City Central Blood Bank",
    status: "ACTIVE",
    joinedAt: "2024-03-04",
  },
  {
    id: "USR-003",
    name: "Nurse Kavya S",
    email: "kavya@apollo.health",
    role: "HOSPITAL_STAFF",
    organization: "Apollo General Hospital",
    status: "ACTIVE",
    joinedAt: "2024-05-21",
  },
  {
    id: "USR-004",
    name: "Ravi Kumar",
    email: "ravi@citybank.health",
    role: "LAB_TECHNICIAN",
    organization: "City Central Blood Bank",
    status: "ACTIVE",
    joinedAt: "2024-06-18",
  },
  {
    id: "USR-005",
    name: "Hariharan B",
    email: "hari@donor.health",
    role: "DONOR",
    organization: "Individual Donor",
    status: "ACTIVE",
    joinedAt: "2025-02-02",
  },
  {
    id: "USR-006",
    name: "Sneha Iyer",
    email: "sneha@donor.health",
    role: "DONOR",
    organization: "Individual Donor",
    status: "SUSPENDED",
    joinedAt: "2025-04-11",
  },
];

export const bloodBanks = [
  {
    id: "BB-01",
    name: "City Central Blood Bank",
    city: "Chennai",
    license: "TN-BB-1042",
    units: 182,
    status: "ACTIVE" as const,
  },
  {
    id: "BB-02",
    name: "Coastal Regional Blood Bank",
    city: "Puducherry",
    license: "PY-BB-0231",
    units: 96,
    status: "ACTIVE" as const,
  },
  {
    id: "BB-03",
    name: "Highland District Blood Bank",
    city: "Coimbatore",
    license: "TN-BB-2210",
    units: 61,
    status: "REVIEW" as const,
  },
];

export const hospitals = [
  {
    id: "HS-01",
    name: "Apollo General Hospital",
    city: "Chennai",
    beds: 640,
    requestsThisMonth: 38,
    status: "ACTIVE" as const,
  },
  {
    id: "HS-02",
    name: "St. Mary Multispeciality",
    city: "Madurai",
    beds: 320,
    requestsThisMonth: 21,
    status: "ACTIVE" as const,
  },
  {
    id: "HS-03",
    name: "Riverside Trauma Centre",
    city: "Trichy",
    beds: 180,
    requestsThisMonth: 44,
    status: "ACTIVE" as const,
  },
];

export const bloodUnits: BloodUnit[] = [
  {
    id: "BU-10241",
    group: "O+",
    donorName: "Hariharan B",
    collectedAt: "2026-08-14",
    expiresAt: "2026-09-18",
    volumeMl: 450,
    status: "AVAILABLE",
    bank: "City Central Blood Bank",
  },
  {
    id: "BU-10242",
    group: "A-",
    donorName: "Sneha Iyer",
    collectedAt: "2026-08-15",
    expiresAt: "2026-09-19",
    volumeMl: 450,
    status: "TESTING",
    bank: "City Central Blood Bank",
  },
  {
    id: "BU-10243",
    group: "B+",
    donorName: "Vikram Sundar",
    collectedAt: "2026-08-11",
    expiresAt: "2026-09-15",
    volumeMl: 350,
    status: "RESERVED",
    bank: "City Central Blood Bank",
  },
  {
    id: "BU-10244",
    group: "AB-",
    donorName: "Fatima Noor",
    collectedAt: "2026-08-09",
    expiresAt: "2026-09-13",
    volumeMl: 450,
    status: "DISPATCHED",
    bank: "Coastal Regional Blood Bank",
  },
  {
    id: "BU-10245",
    group: "O-",
    donorName: "Joseph Antony",
    collectedAt: "2026-08-16",
    expiresAt: "2026-09-20",
    volumeMl: 450,
    status: "TESTING",
    bank: "City Central Blood Bank",
  },
  {
    id: "BU-10246",
    group: "A+",
    donorName: "Divya Menon",
    collectedAt: "2026-07-28",
    expiresAt: "2026-09-01",
    volumeMl: 350,
    status: "DISCARDED",
    bank: "Highland District Blood Bank",
  },
  {
    id: "BU-10247",
    group: "B-",
    donorName: "Karthik Raja",
    collectedAt: "2026-08-17",
    expiresAt: "2026-09-21",
    volumeMl: 450,
    status: "AVAILABLE",
    bank: "City Central Blood Bank",
  },
  {
    id: "BU-10248",
    group: "AB+",
    donorName: "Leela Krishnan",
    collectedAt: "2026-08-18",
    expiresAt: "2026-09-22",
    volumeMl: 450,
    status: "TESTING",
    bank: "City Central Blood Bank",
  },
];

export const TEST_TYPES = ["HIV", "Hepatitis B", "Hepatitis C", "Syphilis", "Malaria"] as const;

export const pendingTests: TestRecord[] = bloodUnits
  .filter((u) => u.status === "TESTING")
  .map((u) => ({
    id: `TST-${u.id.slice(-4)}`,
    unitId: u.id,
    group: u.group,
    collectedAt: u.collectedAt,
    results: Object.fromEntries(TEST_TYPES.map((t) => [t, "PENDING" as const])),
    outcome: "PENDING" as const,
  }));

export const testHistory: TestRecord[] = [
  {
    id: "TST-0231",
    unitId: "BU-10231",
    group: "O+",
    collectedAt: "2026-08-12",
    technician: "Ravi Kumar",
    testedAt: "2026-08-13",
    results: {
      HIV: "PASS",
      "Hepatitis B": "PASS",
      "Hepatitis C": "PASS",
      Syphilis: "PASS",
      Malaria: "PASS",
    },
    outcome: "PASS",
  },
  {
    id: "TST-0232",
    unitId: "BU-10232",
    group: "A+",
    collectedAt: "2026-08-12",
    technician: "Ravi Kumar",
    testedAt: "2026-08-13",
    results: {
      HIV: "PASS",
      "Hepatitis B": "FAIL",
      "Hepatitis C": "PASS",
      Syphilis: "PASS",
      Malaria: "PASS",
    },
    outcome: "FAIL",
    notes: "Reactive HBsAg — unit discarded per protocol.",
  },
  {
    id: "TST-0233",
    unitId: "BU-10233",
    group: "B+",
    collectedAt: "2026-08-14",
    technician: "Ravi Kumar",
    testedAt: "2026-08-15",
    results: {
      HIV: "PASS",
      "Hepatitis B": "PASS",
      "Hepatitis C": "PASS",
      Syphilis: "PASS",
      Malaria: "PASS",
    },
    outcome: "PASS",
  },
];

export const bloodRequests: BloodRequest[] = [
  {
    id: "REQ-5001",
    hospital: "Apollo General Hospital",
    patientRef: "PT-88421",
    group: "O-",
    units: 3,
    urgency: "CRITICAL",
    status: "PENDING",
    requestedBy: "Nurse Kavya S",
    createdAt: "2026-08-19T09:12:00Z",
    neededBy: "2026-08-19T15:00:00Z",
    notes: "Post-partum haemorrhage, theatre 2.",
    timeline: [
      { status: "CREATED", at: "2026-08-19T09:12:00Z", by: "Nurse Kavya S" },
      { status: "PENDING", at: "2026-08-19T09:13:00Z", by: "System", note: "Awaiting blood bank review" },
    ],
  },
  {
    id: "REQ-5002",
    hospital: "Riverside Trauma Centre",
    patientRef: "PT-88410",
    group: "B+",
    units: 2,
    urgency: "HIGH",
    status: "APPROVED",
    requestedBy: "Dr. Sanjay P",
    createdAt: "2026-08-18T17:40:00Z",
    neededBy: "2026-08-19T20:00:00Z",
    timeline: [
      { status: "CREATED", at: "2026-08-18T17:40:00Z", by: "Dr. Sanjay P" },
      { status: "PENDING", at: "2026-08-18T17:41:00Z", by: "System" },
      { status: "APPROVED", at: "2026-08-18T18:20:00Z", by: "Arun Prakash", note: "2 units reserved" },
    ],
  },
  {
    id: "REQ-5003",
    hospital: "St. Mary Multispeciality",
    patientRef: "PT-88377",
    group: "A+",
    units: 1,
    urgency: "NORMAL",
    status: "DISPATCHED",
    requestedBy: "Nurse Kavya S",
    createdAt: "2026-08-18T08:05:00Z",
    neededBy: "2026-08-20T08:00:00Z",
    timeline: [
      { status: "CREATED", at: "2026-08-18T08:05:00Z", by: "Nurse Kavya S" },
      { status: "APPROVED", at: "2026-08-18T09:30:00Z", by: "Arun Prakash" },
      { status: "DISPATCHED", at: "2026-08-18T14:10:00Z", by: "Arun Prakash", note: "Courier BB-Van-04" },
    ],
  },
  {
    id: "REQ-5004",
    hospital: "Apollo General Hospital",
    patientRef: "PT-88301",
    group: "AB+",
    units: 2,
    urgency: "NORMAL",
    status: "COMPLETED",
    requestedBy: "Nurse Kavya S",
    createdAt: "2026-08-15T11:00:00Z",
    neededBy: "2026-08-16T11:00:00Z",
    timeline: [
      { status: "CREATED", at: "2026-08-15T11:00:00Z", by: "Nurse Kavya S" },
      { status: "APPROVED", at: "2026-08-15T12:15:00Z", by: "Arun Prakash" },
      { status: "DISPATCHED", at: "2026-08-15T16:00:00Z", by: "Arun Prakash" },
      { status: "COMPLETED", at: "2026-08-16T09:20:00Z", by: "Nurse Kavya S", note: "Transfused" },
    ],
  },
  {
    id: "REQ-5005",
    hospital: "Riverside Trauma Centre",
    patientRef: "PT-88290",
    group: "AB-",
    units: 4,
    urgency: "HIGH",
    status: "REJECTED",
    requestedBy: "Dr. Sanjay P",
    createdAt: "2026-08-14T22:45:00Z",
    neededBy: "2026-08-15T06:00:00Z",
    timeline: [
      { status: "CREATED", at: "2026-08-14T22:45:00Z", by: "Dr. Sanjay P" },
      { status: "REJECTED", at: "2026-08-14T23:30:00Z", by: "Arun Prakash", note: "Insufficient AB- stock" },
    ],
  },
];

export const camps: Camp[] = [
  {
    id: "CMP-301",
    name: "Anna University Mega Drive",
    organizer: "City Central Blood Bank",
    city: "Chennai",
    address: "CEG Campus, Guindy, Chennai 600025",
    date: "2026-08-28",
    startTime: "09:00",
    endTime: "16:00",
    slots: 200,
    registered: 148,
    status: "UPCOMING",
    description:
      "Annual campus donation drive with 8 collection bays, on-site screening and refreshments.",
  },
  {
    id: "CMP-302",
    name: "IT Park Corporate Camp",
    organizer: "Coastal Regional Blood Bank",
    city: "Puducherry",
    address: "Tidel Park, Block C Atrium",
    date: "2026-09-05",
    startTime: "10:00",
    endTime: "17:00",
    slots: 120,
    registered: 42,
    status: "UPCOMING",
    description: "Corporate donation camp for employees and partner vendors.",
  },
  {
    id: "CMP-303",
    name: "District Hospital Drive",
    organizer: "Highland District Blood Bank",
    city: "Coimbatore",
    address: "Govt. District Hospital, Ward B",
    date: "2026-08-19",
    startTime: "08:30",
    endTime: "14:00",
    slots: 90,
    registered: 90,
    status: "ONGOING",
    description: "Emergency top-up drive triggered by regional O- shortage.",
  },
  {
    id: "CMP-304",
    name: "Temple Festival Camp",
    organizer: "City Central Blood Bank",
    city: "Madurai",
    address: "Meenakshi Temple East Gate",
    date: "2026-07-30",
    startTime: "07:00",
    endTime: "13:00",
    slots: 150,
    registered: 137,
    status: "COMPLETED",
    description: "Festival community camp; 137 units collected.",
  },
];

export const notifications: Notification[] = [
  {
    id: "NTF-901",
    title: "Critical O- shortage in your region",
    body: "Only 9 units of O- remain across 3 partner banks. Emergency SOS broadcast is active.",
    category: "EMERGENCY",
    createdAt: "2026-08-19T10:02:00Z",
    read: false,
  },
  {
    id: "NTF-902",
    title: "New blood request REQ-5001",
    body: "Apollo General Hospital requested 3 units of O- (Critical).",
    category: "REQUEST",
    createdAt: "2026-08-19T09:13:00Z",
    read: false,
  },
  {
    id: "NTF-903",
    title: "Low stock alert: AB-",
    body: "AB- inventory dropped to 4 units, below the threshold of 8.",
    category: "INVENTORY",
    createdAt: "2026-08-19T07:45:00Z",
    read: false,
  },
  {
    id: "NTF-904",
    title: "Camp registration confirmed",
    body: "You are registered for Anna University Mega Drive on 28 Aug 2026.",
    category: "CAMP",
    createdAt: "2026-08-18T13:20:00Z",
    read: true,
  },
  {
    id: "NTF-905",
    title: "Scheduled maintenance",
    body: "Platform maintenance window on 24 Aug 2026, 01:00-02:00 IST.",
    category: "SYSTEM",
    createdAt: "2026-08-17T18:00:00Z",
    read: true,
  },
];

export const donationHistory: DonationRecord[] = [
  { id: "DON-771", date: "2026-05-02", center: "City Central Blood Bank", group: "O+", volumeMl: 450, status: "COMPLETED" },
  { id: "DON-654", date: "2026-01-18", center: "Anna University Mega Drive", group: "O+", volumeMl: 450, status: "COMPLETED" },
  { id: "DON-540", date: "2025-09-27", center: "IT Park Corporate Camp", group: "O+", volumeMl: 350, status: "COMPLETED" },
  { id: "DON-488", date: "2025-06-14", center: "City Central Blood Bank", group: "O+", volumeMl: 0, status: "DEFERRED" },
  { id: "DON-402", date: "2025-02-09", center: "District Hospital Drive", group: "O+", volumeMl: 450, status: "COMPLETED" },
];

export const donorProfile = {
  id: "DNR-1180",
  name: "Hariharan B",
  email: "hari@donor.health",
  phone: "+91 98400 11223",
  group: "O+" as const,
  dob: "2003-04-12",
  gender: "Male",
  weightKg: 72,
  city: "Chennai",
  address: "12/4, Nehru Street, Adyar, Chennai 600020",
  lastDonation: "2026-05-02",
  nextEligible: "2026-08-01",
  totalDonations: 4,
  eligible: true,
  medicalNotes: "No chronic conditions. No medication in the last 6 months.",
};

export const sosBroadcasts: SosBroadcast[] = [
  {
    id: "SOS-2201",
    group: "O-",
    units: 3,
    hospital: "Apollo General Hospital",
    city: "Chennai",
    radiusKm: 15,
    urgency: "CRITICAL",
    status: "ACTIVE",
    createdAt: "2026-08-19T10:00:00Z",
    notified: 214,
    responded: 63,
    accepted: 21,
  },
  {
    id: "SOS-2198",
    group: "AB-",
    units: 2,
    hospital: "Riverside Trauma Centre",
    city: "Trichy",
    radiusKm: 25,
    urgency: "CRITICAL",
    status: "FULFILLED",
    createdAt: "2026-08-16T21:30:00Z",
    notified: 168,
    responded: 41,
    accepted: 12,
  },
  {
    id: "SOS-2190",
    group: "B-",
    units: 1,
    hospital: "St. Mary Multispeciality",
    city: "Madurai",
    radiusKm: 10,
    urgency: "HIGH",
    status: "EXPIRED",
    createdAt: "2026-08-11T04:15:00Z",
    notified: 96,
    responded: 12,
    accepted: 3,
  },
];

export const sosResponses: SosResponse[] = [
  { id: "RSP-01", donorName: "Joseph Antony", group: "O-", distanceKm: 2.4, respondedAt: "2026-08-19T10:06:00Z", answer: "AVAILABLE", phone: "+91 98400 22111" },
  { id: "RSP-02", donorName: "Priya Natarajan", group: "O-", distanceKm: 4.1, respondedAt: "2026-08-19T10:08:00Z", answer: "AVAILABLE", phone: "+91 98400 33122" },
  { id: "RSP-03", donorName: "Mohit Sharma", group: "O-", distanceKm: 6.8, respondedAt: "2026-08-19T10:11:00Z", answer: "UNAVAILABLE", phone: "+91 98400 44233" },
  { id: "RSP-04", donorName: "Anitha Rajan", group: "O-", distanceKm: 8.2, respondedAt: "2026-08-19T10:15:00Z", answer: "AVAILABLE", phone: "+91 98400 55344" },
  { id: "RSP-05", donorName: "Suresh Babu", group: "O-", distanceKm: 11.6, respondedAt: "2026-08-19T10:19:00Z", answer: "NO_RESPONSE", phone: "+91 98400 66455" },
];

export const donationTrends = [
  { month: "Mar", donations: 182, requests: 154 },
  { month: "Apr", donations: 205, requests: 171 },
  { month: "May", donations: 168, requests: 190 },
  { month: "Jun", donations: 221, requests: 203 },
  { month: "Jul", donations: 244, requests: 226 },
  { month: "Aug", donations: 197, requests: 238 },
];

export const sosResponseRate = [
  { month: "Apr", notified: 140, responded: 38 },
  { month: "May", notified: 176, responded: 52 },
  { month: "Jun", notified: 158, responded: 61 },
  { month: "Jul", notified: 190, responded: 74 },
  { month: "Aug", notified: 214, responded: 63 },
];

export const systemActivity = [
  { day: "Mon", logins: 320, actions: 890 },
  { day: "Tue", logins: 412, actions: 1020 },
  { day: "Wed", logins: 386, actions: 964 },
  { day: "Thu", logins: 441, actions: 1180 },
  { day: "Fri", logins: 502, actions: 1310 },
  { day: "Sat", logins: 268, actions: 640 },
  { day: "Sun", logins: 194, actions: 470 },
];

export const auditLogs = [
  { id: "LOG-9001", actor: "Arun Prakash", action: "APPROVED request REQ-5002", target: "REQ-5002", at: "2026-08-18T18:20:00Z", ip: "10.4.2.19" },
  { id: "LOG-9002", actor: "Ravi Kumar", action: "Recorded test result FAIL", target: "BU-10232", at: "2026-08-13T11:02:00Z", ip: "10.4.2.44" },
  { id: "LOG-9003", actor: "Dr. Meera Raghavan", action: "Created blood bank", target: "BB-03", at: "2026-08-12T09:15:00Z", ip: "10.4.1.7" },
  { id: "LOG-9004", actor: "System", action: "SOS broadcast dispatched", target: "SOS-2201", at: "2026-08-19T10:00:00Z", ip: "internal" },
  { id: "LOG-9005", actor: "Nurse Kavya S", action: "Created request REQ-5001", target: "REQ-5001", at: "2026-08-19T09:12:00Z", ip: "10.9.3.21" },
];

export const publicAvailability = BLOOD_GROUPS.map((group) => {
  const stock = bloodStock.find((s) => s.group === group)!;
  const level: "HIGH" | "MODERATE" | "LOW" =
    stock.units >= stock.threshold * 2 ? "HIGH" : stock.units >= stock.threshold ? "MODERATE" : "LOW";
  return { group, units: stock.units, level };
});