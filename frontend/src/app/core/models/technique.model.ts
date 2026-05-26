export interface Technique {
  id: string;
  name: string;
  name_de: string;
  category: 'Emotional' | 'Logisch' | 'Rhetorisch' | 'Strukturell';
  description: string;
  example: string;
  reference_url: string;
}
