export interface FeedbackProblem {
  "Problem Name": string;
  Strengths: string;
  "Areas for Improvement": string;
  "Skill Assessment":
    | "Critical Gap"
    | "Needs Improvement"
    | "Meets Expectations"
    | "Excellent";
  Severity?: "Critical" | "High" | "Moderate" | "Low";
}

export interface SectionFeedback {
  Strengths: string;
  "Areas for Improvement": string;
}

export interface Feedback {
  "Feedback Summary": string;
  "Feedback Details": {
    "Assessment Section": SectionFeedback;
    problems: FeedbackProblem[];
    "Anticipatory Preventative Care Section Feedback": SectionFeedback;
    "Follow Up Care Feedback": SectionFeedback;
    "Overall Recommendations": string;
  };
}
