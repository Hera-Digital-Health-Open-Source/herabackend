from translation_glossary.models import Translation

def translate_entries(entries, from_language, to_language):
  try:
    translations = None
    if from_language == 'en':
      translations = Translation.objects.filter(entry_en__in=entries)
    elif from_language == 'ar':
      translations = Translation.objects.filter(entry_ar__in=entries)
    elif from_language == 'tr':
      translations = Translation.objects.filter(entry_tr__in=entries)
    elif from_language == 'pus':
      translations = Translation.objects.filter(entry_pus__in=entries)
    elif from_language == 'prs':
      translations = Translation.objects.filter(entry_prs__in=entries)
    else:
      return [(x, x) for x in entries]

    if to_language == 'en':
      return translations.values_list(f'entry_{from_language}', 'entry_en')
    elif to_language == 'ar':
      return translations.values_list(f'entry_{from_language}', 'entry_ar')
    elif to_language == 'tr':
      return translations.values_list(f'entry_{from_language}', 'entry_tr')
    elif to_language == 'pus':
      return translations.values_list(f'entry_{from_language}', 'entry_pus')
    elif to_language == 'prs':
      return translations.values_list(f'entry_{from_language}', 'entry_prs')
    else:
      return [(x, x) for x in entries]

  except Translation.DoesNotExist:
      return [(x, x) for x in entries]
